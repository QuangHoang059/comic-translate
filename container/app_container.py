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
from modules.inpainting.factory import InPaintModelFactory
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

    storage_config = providers.Resource(config.storage)

    # Detection module
    detection_processor = providers.Singleton(
        TextBlockDetectorProcessor,
        config=providers.Singleton(
            lambda config: {
                "model": config["detection"]["model"],
                "device": config["detection"]["device"],
                "confidence_threshold": config["detection"]["confidence_threshold"],
                "expansion_percentage": config["detection"]["expansion_percentage"],
            },
            config=config,
        ),
    )

    # OCR module
    ocr_processor = providers.Singleton(
        OCRProcessor,
        config=providers.Singleton(
            lambda config: {
                "model": config["ocr"]["model"],
                "device": config["ocr"]["device"],
                "expansion_percentage": config["ocr"]["expansion_percentage"],
                "source_lang": config["ocr"]["language"],
                "credentials": config.credentials(),
            },
            config=config,
        ),
    )

    # Translation module
    translator = providers.Factory(
        Translator,
        config=providers.Singleton(
            lambda config: {
                "model": config["translation"]["model"],
                "source_lang": config["translation"]["source_lang"],
                "target_lang": config["translation"]["target_lang"],
                "device": config["translation"]["device"],
                "temperature": config["translation"]["temperature"],
                "top_p": config["translation"]["top_p"],
                "max_tokens": config["translation"]["max_tokens"],
                "image_input_enabled": config["translation"]["image_input_enabled"],
                "extra_context": config["translation"]["extra_context"],
                "uppercase": config["translation"]["uppercase"],
                "credentials": config["translation"]["credentials"],
            },
            config=config,
        ),
    )

    # Inpainting module
    inpainter = providers.Singleton(
        lambda config: InPaintModelFactory.create_engine(
            {
                "device": config["inpainting"]["device"],
                "model": config["inpainting"]["model"],
            }
        ),
        config=config,
    )

    # Rendering module
    text_renderer = providers.Singleton(
        TextRenderer,
        config=providers.Singleton(
            lambda config: {
                "font_size": config["rendering"]["font_size"],
                "font_color": config["rendering"]["font_color"],
                "background_color": config["rendering"]["background_color"],
                "line_spacing": config["rendering"]["line_spacing"],
            },
            config=config,
        ),
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
