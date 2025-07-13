from dependency_injector import containers, providers
from dependency_injector.wiring import inject, Provide
import os
import json

# Import các modules
from controller.api_pipeline_controller import APIPipelineController
from modules.detection.processor import TextBlockDetectorProcessor
from modules.ocr.processor import OCRProcessor
from modules.rendering.render_api import TextRenderer
from modules.translation.processor import Translator
from modules.inpainting.processor import InPaintingProcessor
from modules.utils.pipeline_utils import inpaint_map


class AppContainer(containers.DeclarativeContainer):
    """Container chính quản lý dependency injection cho toàn bộ ứng dụng"""

    wiring_config = containers.WiringConfiguration(
        modules=["controller.api_pipeline_controller", "api.router.api", "api.app"]
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

    # Resource config sections
    detection_config = providers.Resource(config.detection)
    ocr_config = providers.Resource(config.ocr)
    translation_config = providers.Resource(config.translation)
    inpainting_config = providers.Resource(config.inpainting)
    rendering_config = providers.Resource(config.rendering)
    storage_config = providers.Resource(config.storage)

    # Modules

    detection_processor = providers.Singleton(
        TextBlockDetectorProcessor,
        config=detection_config,
    )

    ocr_processor = providers.Singleton(
        OCRProcessor,
        config=ocr_config,
    )

    translator = providers.Singleton(
        Translator,
        config=translation_config,
    )

    inpainter = providers.Singleton(
        InPaintingProcessor,
        config=inpainting_config,
    )

    text_renderer = providers.Singleton(
        TextRenderer,
        config=rendering_config,
    )

    # API pipeline (headless version)
    api_pipeline = providers.Singleton(
        APIPipelineController,
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
def get_api_pipeline(api_pipeline=Provide[AppContainer.api_pipeline]):
    return api_pipeline
