# Models for request/response
from pydantic import BaseModel
from typing import List, Optional


class TranslationRequest(BaseModel):
    source_language: str
    target_language: str
    extra_context: Optional[str] = ""
    use_gpu: bool = True


class TextBlockData(BaseModel):
    id: str
    xyxy: List[int]
    text: Optional[str] = None
    translation: Optional[str] = None
    angle: float = 0.0


class ProcessResponse(BaseModel):
    image_id: str
    blocks: List[TextBlockData]
    status: str
