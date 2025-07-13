import cv2
import numpy as np
from typing import List, Optional
from dependency_injector.wiring import inject, Provide

from modules.inpainting.processor import InPaintingProcessor
from modules.rendering.render_api import TextRenderer
from modules.detection.processor import TextBlockDetectorProcessor
from modules.ocr.processor import OCRProcessor
from modules.translation.processor import Translator
from modules.utils.textblock import TextBlock, sort_blk_list
from modules.utils.pipeline_utils import generate_mask, inpaint_map
from modules.utils.translator_utils import set_upper_case


class APIPipelineController:
    """API Pipeline Controller cho headless processing"""

    @inject
    def __init__(
        self,
        detection_processor: TextBlockDetectorProcessor,
        ocr_processor: OCRProcessor,
        translator: Translator,
        inpainter: InPaintingProcessor,
        text_renderer: TextRenderer,
        config=any,
    ):
        self.detection_processor = detection_processor
        self.ocr_processor = ocr_processor
        self.translator = translator
        self.inpainter = inpainter
        self.text_renderer = text_renderer
        self.config = config

        # Initalize
        self.detection_processor.initialize()
        self.ocr_processor.initialize()
        self.translator.initialize()
        self.inpainter.initialize()
        self.text_renderer.initialize()

        # Cache cho các models

    def detect_blocks(self, image: np.ndarray) -> List[TextBlock]:
        """Detect text blocks trong image"""

        blk_list = self.detection_processor.detect(image)
        return blk_list

    def process_ocr(
        self, image: np.ndarray, blk_list: List[TextBlock], source_lang: str
    ) -> List[TextBlock]:
        """Process OCR trên image với text blocks"""

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

        self.translator.translate(blk_list, image, extra_context)

        # Apply uppercase nếu cần
        if self.translator.config.get("uppercase", False):
            set_upper_case(blk_list, True)

        return blk_list

    def inpaint_image(
        self, image: np.ndarray, blk_list: List[TextBlock], use_gpu: bool = False
    ) -> np.ndarray:
        """Inpaint image để xóa text"""
        # Generate mask từ text blocks
        mask = generate_mask(image, blk_list)

        # Inpaint
        from modules.inpainting.schema import Config

        config = Config(hd_strategy="Original")
        inpainted_image = self.inpainter.inpaint(image, mask, config)
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
