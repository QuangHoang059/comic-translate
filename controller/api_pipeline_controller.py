import cv2
import numpy as np
from typing import List, Optional
from dependency_injector.wiring import inject, Provide

from modules.utils.textblock import TextBlock, sort_blk_list
from modules.utils.pipeline_utils import generate_mask, get_language_code, inpaint_map
from modules.utils.translator_utils import set_upper_case
from container.app_container import AppContainer


class APIPipelineController:
    """API Pipeline Controller cho headless processing"""

    @inject
    def __init__(
        self,
        detection_processor=Provide[AppContainer.detection_processor],
        ocr_processor=Provide[AppContainer.ocr_processor],
        translator=Provide[AppContainer.translator],
        inpainter=Provide[AppContainer.inpainter],
        text_renderer=Provide[AppContainer.text_renderer],
        config=Provide[AppContainer.config],
    ):
        self.detection_processor = detection_processor
        self.ocr_processor = ocr_processor
        self.translator = translator
        self.inpainter = inpainter
        self.text_renderer = text_renderer
        self.config = config

        # Cache cho các models
        self.block_detector_cache = None
        self.inpainter_cache = None
        self.cached_inpainter_key = None

    def detect_blocks(self, image: np.ndarray) -> List[TextBlock]:
        """Detect text blocks trong image"""
        if self.block_detector_cache is None:
            self.block_detector_cache = self.detection_processor
            self.block_detector_cache.initialize()

        blk_list = self.block_detector_cache.detect(image)
        return blk_list

    def process_ocr(
        self, image: np.ndarray, blk_list: List[TextBlock], source_lang: str
    ) -> List[TextBlock]:
        """Process OCR trên image với text blocks"""
        # Initialize OCR với config
        ocr_config = {
            "model": self.config.ocr.model(),
            "device": self.config.ocr.device(),
            "expansion_percentage": self.config.ocr.expansion_percentage(),
            "credentials": self.config.credentials(),
        }

        self.ocr_processor.initialize(ocr_config, source_lang)
        self.ocr_processor.process(image, blk_list)

        return blk_list

    def translate_blocks(
        self,
        blk_list: List[TextBlock],
        image: np.ndarray,
        source_lang: str,
        target_lang: str,
        extra_context: str = "",
    ) -> List[TextBlock]:
        """Translate text blocks"""
        # Create translator với languages
        translator_config = {
            "model": self.config.translation.model(),
            "device": self.config.translation.device(),
            "temperature": self.config.translation.temperature(),
            "top_p": self.config.translation.top_p(),
            "max_tokens": self.config.translation.max_tokens(),
            "image_input_enabled": self.config.translation.image_input_enabled(),
            "extra_context": extra_context,
            "uppercase": self.config.translation.uppercase(),
            "credentials": self.config.credentials(),
        }

        translator = self.translator(
            config=translator_config,
            main_page=None,
            source_lang=source_lang,
            target_lang=target_lang,
        )

        translator.translate(blk_list, image, extra_context)

        # Apply uppercase nếu cần
        if translator_config.get("uppercase", False):
            set_upper_case(blk_list, True)

        return blk_list

    def inpaint_image(
        self, image: np.ndarray, blk_list: List[TextBlock], use_gpu: bool = False
    ) -> np.ndarray:
        """Inpaint image để xóa text"""
        # Generate mask từ text blocks
        mask = generate_mask(image, blk_list)

        # Get inpainter
        if (
            self.inpainter_cache is None
            or self.cached_inpainter_key != self.config.inpainting.model()
        ):

            device = "cuda" if use_gpu else "cpu"
            inpainter_key = self.config.inpainting.model()
            InpainterClass = inpaint_map[inpainter_key]
            self.inpainter_cache = InpainterClass(device)
            self.cached_inpainter_key = inpainter_key

        # Inpaint
        from modules.inpainting.schema import Config

        config = Config(hd_strategy="Original")
        inpainted_image = self.inpainter_cache(image, mask, config)
        inpainted_image = cv2.convertScaleAbs(inpainted_image)

        return inpainted_image

    def render_text(self, image: np.ndarray, blk_list: List[TextBlock]) -> np.ndarray:
        """Render translated text lên image"""
        return self.text_renderer.render_text(image, blk_list)

    def process_full_pipeline(
        self,
        image: np.ndarray,
        source_lang: str,
        target_lang: str,
        extra_context: str = "",
        use_gpu: bool = False,
    ) -> dict:
        """Process toàn bộ pipeline: detect -> OCR -> translate -> inpaint -> render"""

        # Step 1: Detect blocks
        blk_list = self.detect_blocks(image)

        # Step 2: OCR
        blk_list = self.process_ocr(image, blk_list, source_lang)

        # Step 3: Translate
        blk_list = self.translate_blocks(
            blk_list, image, source_lang, target_lang, extra_context
        )

        # Step 4: Inpaint
        inpainted_image = self.inpaint_image(image, blk_list, use_gpu)

        # Step 5: Render text
        final_image = self.render_text(inpainted_image, blk_list)

        return {
            "original_image": image,
            "inpainted_image": inpainted_image,
            "final_image": final_image,
            "text_blocks": blk_list,
        }

    def process_step_by_step(
        self,
        image: np.ndarray,
        source_lang: str,
        target_lang: str,
        step: str,
        blk_list: Optional[List[TextBlock]] = None,
        extra_context: str = "",
        use_gpu: bool = False,
    ) -> dict:
        """Process từng step riêng biệt"""

        if step == "detect":
            blk_list = self.detect_blocks(image)
            return {"text_blocks": blk_list, "status": "detected"}

        elif step == "ocr":
            if blk_list is None:
                raise ValueError("Text blocks required for OCR step")
            blk_list = self.process_ocr(image, blk_list, source_lang)
            return {"text_blocks": blk_list, "status": "ocr_completed"}

        elif step == "translate":
            if blk_list is None:
                raise ValueError("Text blocks required for translation step")
            blk_list = self.translate_blocks(
                blk_list, image, source_lang, target_lang, extra_context
            )
            return {"text_blocks": blk_list, "status": "translated"}

        elif step == "inpaint":
            if blk_list is None:
                raise ValueError("Text blocks required for inpainting step")
            inpainted_image = self.inpaint_image(image, blk_list, use_gpu)
            return {"inpainted_image": inpainted_image, "status": "inpainted"}

        elif step == "render":
            if blk_list is None:
                raise ValueError("Text blocks required for rendering step")
            final_image = self.render_text(image, blk_list)
            return {"final_image": final_image, "status": "rendered"}

        else:
            raise ValueError(f"Unknown step: {step}")
