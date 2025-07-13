import numpy as np
from typing import Any

from ..utils.textblock import TextBlock
from ..utils.pipeline_utils import language_codes
from .factory import OCRFactory


class OCRProcessor:
    """
    Processor for OCR operations using various engines.

    Uses a factory pattern to create and utilize the appropriate OCR engine
    based on settings and language.
    """

    def __init__(self, config: dict = {}):
        self.config: dict = config
        self.source_lang = None
        self.source_lang_english = None

    def initialize(self, config: dict = {}) -> None:
        """
        Initialize the OCR processor with settings and language.

        Args:
            config: The main application page with settings
        """
        if config:
            self.config = config

        self.source_lang = self.config.get("languages")
        self.source_lang_english = self._get_english_lang(self.source_lang)
        self.ocr_model = self._get_ocr_key(self.config.get("model"))

    def _get_english_lang(self, translated_lang: str) -> str:
        return self.config.get(translated_lang, translated_lang)

    def process(self, img: np.ndarray, blk_list: list[TextBlock]) -> list[TextBlock]:
        """
        Process image with appropriate OCR engine.

        Args:
            img: Input image as numpy array
            blk_list: List of TextBlock objects to update with OCR text

        Returns:
            Updated list of TextBlock objects with recognized text
        """
        # Set language code for each text block
        self._set_source_language(blk_list)

        try:
            # Get appropriate OCR engine from factory
            engine = OCRFactory.create_engine(
                self.config, self.source_lang_english, self.ocr_model
            )

            # Process image with selected engine
            return engine.process_image(img, blk_list)

        except Exception as e:
            print(f"OCR processing error: {str(e)}")
            return blk_list

    def _set_source_language(self, blk_list: list[TextBlock]) -> None:
        source_lang_code = language_codes.get(self.source_lang_english, "en")
        for blk in blk_list:
            blk.source_lang = source_lang_code

    def _get_ocr_key(self, localized_ocr: str) -> str:
        translator_map = {
            "GPT-4.1-mini": "GPT-4.1-mini",
            "Microsoft OCR": "Microsoft OCR",
            "Google Cloud Vision": "Google Cloud Vision",
            "Gemini-2.0-Flash": "Gemini-2.0-Flash",
            "Default": "Default",
        }
        return translator_map.get(localized_ocr, localized_ocr)
