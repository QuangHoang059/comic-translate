import json
import hashlib

from .base import TranslationEngine
from .google import GoogleTranslation
from .microsoft import MicrosoftTranslation
from .deepl import DeepLTranslation
from .yandex import YandexTranslation
from .llm.gpt import GPTTranslation
from .llm.claude import ClaudeTranslation
from .llm.gemini import GeminiTranslation
from .llm.deepseek import DeepseekTranslation
from .llm.custom import CustomTranslation


class TranslationFactory:
    """Factory for creating appropriate translation engines based on config."""

    _engines = {}  # Cache of created engines

    # Map traditional translation services to their engine classes
    TRADITIONAL_ENGINES = {
        "Google Translate": GoogleTranslation,
        "Microsoft Translator": MicrosoftTranslation,
        "DeepL": DeepLTranslation,
        "Yandex": YandexTranslation,
    }

    # Map LLM identifiers to their engine classes
    LLM_ENGINE_IDENTIFIERS = {
        "GPT": GPTTranslation,
        "Claude": ClaudeTranslation,
        "Gemini": GeminiTranslation,
        "Deepseek": DeepseekTranslation,
        "Custom": CustomTranslation,
    }

    # Default engines for fallback
    DEFAULT_TRADITIONAL_ENGINE = GoogleTranslation
    DEFAULT_LLM_ENGINE = GPTTranslation

    @classmethod
    def create_engine(
        cls, config: dict, source_lang: str, target_lang: str, translator_model: str
    ) -> TranslationEngine:
        """
        Create or retrieve an appropriate translation engine based on config.

        Args:
            config: config object with translation configuration
            source_lang: Source language name
            target_lang: Target language name
            translator_model: Key identifying which translator to use

        Returns:
            Appropriate translation engine instance
        """
        # Create a cache key based on translator and language pair
        cache_key = cls._create_cache_key(
            translator_model, source_lang, target_lang, config
        )

        # Return cached engine if available
        if cache_key in cls._engines:
            return cls._engines[cache_key]

        # Determine engine class and create engine
        engine_class = cls._get_engine_class(translator_model)
        engine = engine_class()

        # Initialize with appropriate parameters
        if translator_model in cls.TRADITIONAL_ENGINES:
            engine.initialize(config, source_lang, target_lang)
        else:
            engine.initialize(config, source_lang, target_lang, translator_model)

        # Cache the engine
        cls._engines[cache_key] = engine
        return engine

    @classmethod
    def _get_engine_class(cls, translator_model: str):
        """Get the appropriate engine class based on translator key."""
        # First check if it's a traditional translation engine (exact match)
        if translator_model in cls.TRADITIONAL_ENGINES:
            return cls.TRADITIONAL_ENGINES[translator_model]

        # Otherwise look for matching LLM engine (substring match)
        for identifier, engine_class in cls.LLM_ENGINE_IDENTIFIERS.items():
            if identifier in translator_model:
                return engine_class

        # Default to LLM engine if no match found
        return cls.DEFAULT_LLM_ENGINE

    @classmethod
    def _create_cache_key(
        cls, translator_model: str, source_lang: str, target_lang: str, config: dict
    ) -> str:
        """
        Build a cache key for all translation engines.

        - Always includes per-translator credentials (if available),
          so changing any API key, URL, region, etc. triggers a new engine.
        - For LLM engines, also includes all LLM-specific config
          (temperature, top_p, context, etc.).
        - The cache key is a hash of these dynamic values, combined with
          the translator key and language pair.
        - If no dynamic values are found, falls back to a simple key
          based on translator and language pair.
        """
        base = f"{translator_model}_{source_lang}_{target_lang}"

        # Gather any dynamic bits we care about:
        extras = {}

        # Always grab credentials for this service (if any)
        creds = config.get("credentials")
        if creds:
            extras["credentials"] = creds

        # If it's an LLM, also grab the llm config
        is_llm = any(
            identifier in translator_model for identifier in cls.LLM_ENGINE_IDENTIFIERS
        )
        if is_llm:
            extras["llm"] = config.get("llm_config") or dict()

        if not extras:
            return base

        # Otherwise, hash the combined extras dict
        extras_json = json.dumps(
            extras, sort_keys=True, separators=(",", ":"), default=str
        )
        digest = hashlib.sha256(extras_json.encode("utf-8")).hexdigest()

        # Append the fingerprint
        return f"{base}_{digest}"
