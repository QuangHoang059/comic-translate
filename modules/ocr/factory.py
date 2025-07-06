import json
import hashlib

from .base import OCREngine
from .microsoft_ocr import MicrosoftOCR
from .google_ocr import GoogleOCR
from .gpt_ocr import GPTOCR
from .paddle_ocr import PaddleOCREngine
from .manga_ocr.engine import MangaOCREngine
from .pororo.engine import PororoOCREngine
from .doctr_ocr import DocTROCR
from .gemini_ocr import GeminiOCR

class OCRFactory:
    """Factory for creating appropriate OCR engines based on config."""
    
    _engines = {}  # Cache of created engines

    LLM_ENGINE_IDENTIFIERS = {
        "GPT": GPTOCR,
        "Gemini": GeminiOCR,
    }
    
    @classmethod
    def create_engine(cls, config:dict, source_lang_english: str, ocr_model: str) -> OCREngine:
        """
        Create or retrieve an appropriate OCR engine based on config.
        
        Args:
            config: config object with OCR configuration
            source_lang_english: Source language in English
            ocr_model: OCR model to use
            
        Returns:
            Appropriate OCR engine instance
        """
        # Create a cache key based on model and language
        cache_key = cls._create_cache_key(ocr_model, source_lang_english, config)
        
        # Return cached engine if available
        if cache_key in cls._engines:
            return cls._engines[cache_key]
        
        # Create engine based on model or language
        engine = cls._create_new_engine(config, source_lang_english, ocr_model)
        cls._engines[cache_key] = engine
        return engine
    
    @classmethod
    def _create_cache_key(cls, ocr_model: str,
                        source_lang: str,
                        config: dict) -> str:
        """
        Build a cache key for all ocr engines.

        - Always includes per-ocr credentials (if available),
          so changing any API key, URL, region, etc. triggers a new engine.
        - For LLM engines, also includes all LLM-specific config
          (temperature, top_p, context, etc.).
        - The cache key is a hash of these dynamic values, combined with
          the ocr key and source language.
        - If no dynamic values are found, falls back to a simple key
          based on ocr and source language.
        """
        base = f"{ocr_model}_{source_lang}"

        # Gather any dynamic bits we care about:
        extras = {}

        # Always grab credentials for this service (if any)
        creds = config.get("credentials")
        if creds:
            extras["credentials"] = creds


        if not extras:
            return base

        # Otherwise, hash the combined extras dict
        extras_json = json.dumps(
            extras,
            sort_keys=True,
            separators=(",", ":"),
            default=str
        )
        digest = hashlib.sha256(extras_json.encode("utf-8")).hexdigest()

        # Append the fingerprint
        return f"{base}_{digest}"
    
    @classmethod
    def _create_new_engine(cls, config:dict, source_lang_english: str, ocr_model: str) -> OCREngine:
        """Create a new OCR engine instance based on model and language."""
        
        # Model-specific factory functions
        general = {
            'Microsoft OCR': cls._create_microsoft_ocr,
            'Google Cloud Vision': cls._create_google_ocr,
            'GPT-4.1-mini': lambda s: cls._create_gpt_ocr(s, ocr_model),
            'Gemini-2.0-Flash': lambda s: cls._create_gemini_ocr(s, ocr_model)
        }
        
        # Language-specific factory functions (for Default model)
        language_factories = {
            'Japanese': cls._create_manga_ocr,
            'Korean': cls._create_pororo_ocr,
            'Chinese': cls._create_paddle_ocr,
            'Russian': lambda s: cls._create_gpt_ocr(s, 'GPT-4.1-mini')
        }
        
        # Check if we have a specific model factory
        if ocr_model in general:
            return general[ocr_model](config)
        
        # For Default, use language-specific engines
        if ocr_model == 'Default' and source_lang_english in language_factories:
            return language_factories[source_lang_english](config)
        
        # Fallback to doctr for any other language
        return cls._create_doctr_ocr(config)
    
    @staticmethod
    def _create_microsoft_ocr(config:dict) -> OCREngine:
        engine = MicrosoftOCR()
        credentials = config.get("credentials")
        engine.initialize(
            api_key=credentials['api_key'],
            endpoint=credentials['endpoint']
        )
        return engine
    
    @staticmethod
    def _create_google_ocr(config:dict) -> OCREngine:
        engine = GoogleOCR()
        credentials = config.get("credentials")
        engine.initialize(api_key=credentials['api_key'])
        return engine
    
    @staticmethod
    def _create_gpt_ocr(config:dict, model) -> OCREngine:
        engine = GPTOCR()
        credentials = config.get("credentials")
        api_key = credentials.get('api_key', '')
        expansion_percentage = config.get('expansion_percentage', 0)
        engine.initialize(api_key=api_key, model=model, expansion_percentage=expansion_percentage)
        return engine
    
    @staticmethod
    def _create_manga_ocr(config:dict) -> OCREngine:
        engine = MangaOCREngine()
        device = config.get('device', 'cpu')
        expansion_percentage = config.get('expansion_percentage', 5)
        engine.initialize(device=device,expansion_percentage=expansion_percentage)
        return engine
    
    @staticmethod
    def _create_pororo_ocr(config:dict) -> OCREngine:
        engine = PororoOCREngine()
        lang = config.get('lang', 'ko')
        engine.initialize(lang=lang)
        return engine
    
    @staticmethod
    def _create_paddle_ocr(config:dict) -> OCREngine:
        engine = PaddleOCREngine()
        lang = config.get('lang', 'ch')
        engine.initialize(lang=lang)
        return engine
    
    @staticmethod
    def _create_doctr_ocr(config:dict) -> OCREngine:
        engine = DocTROCR()
        device = config.get('device', 'cpu')
        engine.initialize(device=device)
        return engine
    
    @staticmethod
    def _create_gemini_ocr(config:dict, model) -> OCREngine:
        engine = GeminiOCR()
        credentials = config.get("credentials")
        api_key = credentials.get('api_key', '')
        expansion_percentage=config.get('expansion_percentage', 5)
        engine.initialize(api_key=api_key, model=model, expansion_percentage=expansion_percentage)
        return engine