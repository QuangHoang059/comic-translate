from dependency_injector import containers, providers
from dependency_injector.wiring import inject, Provide
import os
import json

# Import các modules
from modules.detection.processor import TextBlockDetectorProcessor
from modules.ocr.processor import OCRProcessor
from modules.translation.processor import Translator
from modules.inpainting.factory import InPaintModelFactory
from modules.utils.pipeline_utils import inpaint_map


class TextRenderer:
    """Class để render text lên image"""

    def __init__(self, config: dict):
        self.config = config
        self.font_size = config.get("font_size", 12)
        self.font_color = config.get("font_color", "#000000")
        self.background_color = config.get("background_color", "#FFFFFF")
        self.line_spacing = config.get("line_spacing", 1.2)

    def render_text(self, image, text_blocks):
        """Render text lên image"""
        # Implementation sẽ được thêm sau
        return image


class AppContainer(containers.DeclarativeContainer):
    """Container chính quản lý dependency injection cho toàn bộ ứng dụng"""

    wiring_config = containers.WiringConfiguration(
        modules=[
            "controller.translate_controler",
            "controller.api_pipeline_controller",
            "api.router.api",
            "modules.detection.processor",
            "modules.ocr.processor",
            "modules.translation.processor",
            "modules.inpainting.factory",
            "modules.rendering.render",
        ]
    )
    # Configuration
    config = providers.Configuration()

    # Load config từ file
    @classmethod
    def load_config(cls, config_path: str = "config/config.json"):
        """Load configuration từ file JSON"""
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            cls.config.from_dict(config_data)
        else:
            # Default config nếu file không tồn tại
            cls.config.from_dict(
                {
                    "app": {
                        "name": "Comic Translate",
                        "version": "1.0.0",
                        "debug": False,
                    },
                    "detection": {
                        "model": "RT-DETR-V2",
                        "device": "cpu",
                        "confidence_threshold": 0.3,
                    },
                    "ocr": {
                        "model": "Default",
                        "device": "cpu",
                        "expansion_percentage": 5,
                    },
                    "translation": {
                        "model": "GPT-4o",
                        "device": "cpu",
                        "temperature": 1.0,
                    },
                    "inpainting": {"model": "lama", "device": "cpu"},
                    "rendering": {"font_size": 12, "font_color": "#000000"},
                    "credentials": {},
                    "storage": {
                        "upload_dir": "uploads",
                        "results_dir": "results",
                        "models_dir": "models",
                    },
                }
            )

    # Storage providers
    upload_dir = providers.Singleton(
        lambda config: config.storage.upload_dir(), config=config
    )

    results_dir = providers.Singleton(
        lambda config: config.storage.results_dir(), config=config
    )

    models_dir = providers.Singleton(
        lambda config: config.storage.models_dir(), config=config
    )

    # Detection module
    detection_processor = providers.Singleton(
        TextBlockDetectorProcessor,
        config=providers.Singleton(
            lambda config: {
                "model": config.detection.model(),
                "device": config.detection.device(),
                "confidence_threshold": config.detection.confidence_threshold(),
                "expansion_percentage": config.detection.expansion_percentage(),
            },
            config=config,
        ),
    )

    # OCR module
    ocr_processor = providers.Singleton(OCRProcessor)

    # Translation module
    translator = providers.Factory(
        Translator,
        config=providers.Singleton(
            lambda config: {
                "model": config.translation.model(),
                "device": config.translation.device(),
                "temperature": config.translation.temperature(),
                "top_p": config.translation.top_p(),
                "max_tokens": config.translation.max_tokens(),
                "image_input_enabled": config.translation.image_input_enabled(),
                "extra_context": config.translation.extra_context(),
                "uppercase": config.translation.uppercase(),
                "credentials": config.credentials(),
            },
            config=config,
        ),
        main_page=None,  # Sẽ được inject khi cần
        source_lang="",
        target_lang="",
    )

    # Inpainting module
    inpainter = providers.Singleton(
        lambda config: InPaintModelFactory.create_engine(
            {"device": config.inpainting.device()}, config.inpainting.model()
        ),
        config=config,
    )

    # Rendering module
    text_renderer = providers.Singleton(
        TextRenderer,
        config=providers.Singleton(
            lambda config: {
                "font_size": config.rendering.font_size(),
                "font_color": config.rendering.font_color(),
                "background_color": config.rendering.background_color(),
                "line_spacing": config.rendering.line_spacing(),
            },
            config=config,
        ),
    )

    # Pipeline controller
    pipeline_controller = providers.Singleton(
        "controller.translate_controler.ComicTranslateControler",
        main_page=None,  # Sẽ được inject khi cần
        detection_processor=detection_processor,
        ocr_processor=ocr_processor,
        translator=translator,
        inpainter=inpainter,
        text_renderer=text_renderer,
    )

    # API pipeline (headless version)
    api_pipeline = providers.Singleton(
        "controller.api_pipeline_controller.APIPipelineController",
        detection_processor=detection_processor,
        ocr_processor=ocr_processor,
        translator=translator,
        inpainter=inpainter,
        text_renderer=text_renderer,
        config=config,
    )


# Helper functions để inject dependencies
@inject
def get_detection_processor(
    detection_processor: TextBlockDetectorProcessor = Provide[
        AppContainer.detection_processor
    ],
) -> TextBlockDetectorProcessor:
    return detection_processor


@inject
def get_ocr_processor(
    ocr_processor: OCRProcessor = Provide[AppContainer.ocr_processor],
) -> OCRProcessor:
    return ocr_processor


@inject
def get_translator(
    translator: Translator = Provide[AppContainer.translator],
) -> Translator:
    return translator


@inject
def get_inpainter(inpainter=Provide[AppContainer.inpainter]):
    return inpainter


@inject
def get_text_renderer(text_renderer=Provide[AppContainer.text_renderer]):
    return text_renderer


@inject
def get_pipeline_controller(
    pipeline_controller=Provide[AppContainer.pipeline_controller],
):
    return pipeline_controller


@inject
def get_api_pipeline(api_pipeline=Provide[AppContainer.api_pipeline]):
    return api_pipeline
