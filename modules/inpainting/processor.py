import numpy as np
from modules.inpainting.factory import InPaintModelFactory
from .schema import Config


class InPaintingProcessor:

    def __init__(self, config: dict):
        self.engine = None
        self.config = config
        self.model = "LaMa"

    def initialize(self, config: dict = {}) -> None:
        if config:
            self.config = config

        self.model = self.config.get("model") or self.model
        # Create appropriate engine
        self.engine = InPaintModelFactory.create_engine(self.config, self.model)

    def inpaint(self, img: np.ndarray, mask: np.ndarray, config: Config) -> np.ndarray:
        if self.engine is None:
            self.initialize()

        if self.engine is None:
            raise ValueError("Inpaint engine not initialized")
        return self.engine(img, mask, config)
