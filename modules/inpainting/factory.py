from modules.inpainting.base import InpaintModel
from modules.utils.pipeline_utils import inpaint_map

class InPaintModelFactory:
    _model = {}
    def __init__(self):
        self.model = None
    @classmethod
    def create_engine(cls, config:dict, model_name: str = 'LaMa') -> InpaintModel:
        """
        Create or retrieve an appropriate detection engine.
        
        Args:
            config: config object with detection configuration
            model_name: Name of the detection model to use
            
        Returns:
            Appropriate detection engine instance
        """
        # Create a cache key based on model
        cache_key = f"{model_name}"
        
        # Return cached engine if available
        if cache_key in cls._model:
            return cls._model[cache_key]
        

        # Get the appropriate factory method, defaulting to LaMa
        factory_method = inpaint_map.get(model_name, 'LaMa')
        
        # Create and cache the engine
        engine = factory_method(device=config.get('device', 'cpu'))
        cls._model[cache_key] = engine
        return engine
    