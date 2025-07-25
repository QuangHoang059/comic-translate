from typing import Any

from .gpt import GPTTranslation
from ...utils.translator_utils import MODEL_MAP


class DeepseekTranslation(GPTTranslation):
    """Translation engine using Deepseek models with OpenAI-compatible API."""

    def __init__(self):
        super().__init__()
        self.supports_images = False
        self.api_base_url = "https://api.deepseek.com/v1"

    def initialize(
        self,
        config: dict,
        source_lang: str,
        target_lang: str,
        model_name: str,
        **kwargs
    ) -> None:
        """
        Initialize Deepseek translation engine.

        Args:
            config: config object with credentials
            source_lang: Source language name
            target_lang: Target language name
            model_name: Deepseek model name
        """
        # Call BaseLLMTranslation's initialize
        super(GPTTranslation, self).initialize(
            config, source_lang, target_lang, **kwargs
        )

        self.model_name = model_name
        credentials = config.get("credentials")
        self.api_key = credentials.get("api_key", "")
        self.model = MODEL_MAP.get(self.model_name)
