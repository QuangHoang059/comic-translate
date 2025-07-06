from typing import Any
from .gpt import GPTTranslation


class CustomTranslation(GPTTranslation):
    """Translation engine using custom LLM configurations with OpenAI-compatible API."""

    def __init__(self):
        super().__init__()

    def initialize(
        self, config: dict, source_lang: str, target_lang: str, tr_key: str, **kwargs
    ) -> None:
        """
        Initialize custom translation engine.

        Args:
            config: config object with credentials
            source_lang: Source language name
            target_lang: Target language name
        """
        # Call BaseLLMTranslation's initialize, not GPTTranslation's
        # to avoid the GPT-specific credential loading
        super(GPTTranslation, self).initialize(
            config, source_lang, target_lang, **kwargs
        )

        # Get custom credentials instead of OpenAI credentials
        credentials = config.get("credentials")
        self.api_key = credentials.get("api_key", "")
        self.model = credentials.get("model", "")

        # Override the API base URL with the custom one
        self.api_base_url = credentials.get("api_url", "").rstrip("/")
