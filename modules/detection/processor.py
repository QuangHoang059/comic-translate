import numpy as np

from ..utils.textblock import TextBlock
from .factory import DetectionEngineFactory


class TextBlockDetectorProcessor:
    """
    model for finding text blocks in images.
    """

    def __init__(self, config: dict):
        self.config = config
        self.engine = None
        self.model = "RT-DETR-V2"  # Default model

    def initialize(self, config: dict = {}) -> None:
        if config:
            self.config = config

        self.model = self.config.get("model") or self.model
        # Create appropriate engine
        self.engine = DetectionEngineFactory.create_engine(self.config, self.model)

    def detect(self, img: np.ndarray) -> list[TextBlock]:
        if self.engine is None:
            self.initialize()

        if self.engine is None:
            raise ValueError("Detection engine not initialized")

        return self.engine.detect(img)
