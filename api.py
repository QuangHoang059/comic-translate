import os
import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File, Form, APIRouter, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid
import shutil
from datetime import datetime

from pipeline import ComicTranslatePipeline
from modules.utils.textblock import TextBlock
from modules.utils.pipeline_utils import generate_mask, get_language_code

# Models for request/response
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

# Create FastAPI app
app = FastAPI(title="Comic Translate API")
router = APIRouter(prefix="/api/v1", tags=["translation"])

# Storage for uploaded images and results
UPLOAD_DIR = "uploads"
RESULTS_DIR = "results"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# In-memory storage for processing state
image_store = {}

# Initialize pipeline
pipeline = ComicTranslatePipeline(None)  # We'll need to adapt this for API use

@router.post("/upload", response_model=ProcessResponse)
async def upload_image(
    file: UploadFile = File(...),
    source_language: str = Form(...),
    target_language: str = Form(...)
):
    # Generate unique ID for this image
    image_id = str(uuid.uuid4())
    
    # Save uploaded file
    file_path = os.path.join(UPLOAD_DIR, f"{image_id}{os.path.splitext(file.filename)[1]}")
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    # Store image info
    image_store[image_id] = {
        "path": file_path,
        "source_language": source_language,
        "target_language": target_language,
        "status": "uploaded"
    }
    
    return ProcessResponse(
        image_id=image_id,
        blocks=[],
        status="uploaded"
    )

@router.post("/detect-blocks/{image_id}", response_model=ProcessResponse)
async def detect_blocks(image_id: str):
    if image_id not in image_store:
        return JSONResponse(status_code=404, content={"error": "Image not found"})
    
    # Load image
    image_path = image_store[image_id]["path"]
    image = cv2.imread(image_path)
    
    # Detect blocks
    if pipeline.block_detector_cache is None:
        pipeline.block_detector_cache = TextBlockDetectorProcessor(None)  # Adapt for API use
    
    blk_list = pipeline.block_detector_cache.detect(image)
    
    # Convert blocks to response format
    blocks = []
    for i, blk in enumerate(blk_list):
        blocks.append(TextBlockData(
            id=f"{i}",
            xyxy=blk.xyxy,
            angle=blk.angle
        ))
    
    # Update image store
    image_store[image_id]["blocks"] = blk_list
    image_store[image_id]["status"] = "blocks_detected"
    
    return ProcessResponse(
        image_id=image_id,
        blocks=blocks,
        status="blocks_detected"
    )

@router.post("/ocr/{image_id}", response_model=ProcessResponse)
async def ocr_image(image_id: str):
    if image_id not in image_store:
        return JSONResponse(status_code=404, content={"error": "Image not found"})
    
    if "blocks" not in image_store[image_id]:
        return JSONResponse(status_code=400, content={"error": "Blocks not detected yet"})
    
    # Load image and blocks
    image_path = image_store[image_id]["path"]
    image = cv2.imread(image_path)
    blk_list = image_store[image_id]["blocks"]
    source_lang = image_store[image_id]["source_language"]
    
    # Initialize OCR
    pipeline.ocr.initialize(None, source_lang)  # Adapt for API use
    
    # Process OCR
    pipeline.ocr.process(image, blk_list)
    
    # Convert blocks to response format
    blocks = []
    for i, blk in enumerate(blk_list):
        blocks.append(TextBlockData(
            id=f"{i}",
            xyxy=blk.xyxy,
            text=blk.text,
            angle=blk.angle
        ))
    
    # Update image store
    image_store[image_id]["status"] = "ocr_completed"
    
    return ProcessResponse(
        image_id=image_id,
        blocks=blocks,
        status="ocr_completed"
    )

@router.post("/translate/{image_id}", response_model=ProcessResponse)
async def translate_image(image_id: str, request: TranslationRequest):
    if image_id not in image_store:
        return JSONResponse(status_code=404, content={"error": "Image not found"})
    
    if "blocks" not in image_store[image_id]:
        return JSONResponse(status_code=400, content={"error": "Blocks not detected yet"})
    
    # Load image and blocks
    image_path = image_store[image_id]["path"]
    image = cv2.imread(image_path)
    blk_list = image_store[image_id]["blocks"]
    
    # Initialize translator
    translator = Translator(None, request.source_language, request.target_language)  # Adapt for API use
    
    # Translate
    translator.translate(blk_list, image, request.extra_context)
    
    # Convert blocks to response format
    blocks = []
    for i, blk in enumerate(blk_list):
        blocks.append(TextBlockData(
            id=f"{i}",
            xyxy=blk.xyxy,
            text=blk.text,
            translation=blk.translation,
            angle=blk.angle
        ))
    
    # Update image store
    image_store[image_id]["status"] = "translated"
    
    return ProcessResponse(
        image_id=image_id,
        blocks=blocks,
        status="translated"
    )

@router.post("/inpaint/{image_id}")
async def inpaint_image(image_id: str, background_tasks: BackgroundTasks):
    if image_id not in image_store:
        return JSONResponse(status_code=404, content={"error": "Image not found"})
    
    if "blocks" not in image_store[image_id]:
        return JSONResponse(status_code=400, content={"error": "Blocks not detected yet"})
    
    # Load image and blocks
    image_path = image_store[image_id]["path"]
    image = cv2.imread(image_path)
    blk_list = image_store[image_id]["blocks"]
    
    # Generate mask
    mask = generate_mask(image, blk_list)
    
    # Inpaint
    if pipeline.inpainter_cache is None:
        device = 'cuda' if request.use_gpu else 'cpu'
        inpainter_key = "lama"  # Default or configurable
        InpainterClass = inpaint_map[inpainter_key]
        pipeline.inpainter_cache = InpainterClass(device)
        pipeline.cached_inpainter_key = inpainter_key
    
    config = {}  # Configure as needed
    inpainted_image = pipeline.inpainter_cache(image, mask, config)
    inpainted_image = cv2.convertScaleAbs(inpainted_image)
    
    # Save inpainted image
    result_path = os.path.join(RESULTS_DIR, f"{image_id}_inpainted.jpg")
    cv2.imwrite(result_path, inpainted_image)
    
    # Update image store
    image_store[image_id]["inpainted_path"] = result_path
    image_store[image_id]["status"] = "inpainted"
    
    return {"image_id": image_id, "status": "inpainted", "result_path": result_path}

@router.post("/render/{image_id}")
async def render_translated_image(image_id: str):
    if image_id not in image_store:
        return JSONResponse(status_code=404, content={"error": "Image not found"})
    
    if "inpainted_path" not in image_store[image_id]:
        return JSONResponse(status_code=400, content={"error": "Image not inpainted yet"})
    
    # Load inpainted image
    inpainted_path = image_store[image_id]["inpainted_path"]
    inpainted_image = cv2.imread(inpainted_path)
    
    # Get blocks
    blk_list = image_store[image_id]["blocks"]
    
    # Render text on image
    # This would need to be adapted from the UI rendering to a headless version
    # For now, we'll just return the inpainted image
    
    # Save rendered image
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_path = os.path.join(RESULTS_DIR, f"{image_id}_translated_{timestamp}.jpg")
    cv2.imwrite(result_path, inpainted_image)
    
    return {"image_id": image_id, "status": "rendered", "result_path": result_path}

@router.get("/result/{image_id}")
async def get_result_image(image_id: str):
    if image_id not in image_store:
        return JSONResponse(status_code=404, content={"error": "Image not found"})
    
    status = image_store[image_id]["status"]
    
    if status == "inpainted" and "inpainted_path" in image_store[image_id]:
        return FileResponse(image_store[image_id]["inpainted_path"])
    elif status == "rendered" and "rendered_path" in image_store[image_id]:
        return FileResponse(image_store[image_id]["rendered_path"])
    else:
        return JSONResponse(status_code=400, content={"error": f"No result available. Current status: {status}"})

@router.post("/translate-all/{image_id}", response_model=ProcessResponse)
async def translate_all_steps(image_id: str, request: TranslationRequest, background_tasks: BackgroundTasks):
    """Process all steps at once: detect blocks, OCR, translate, inpaint, and render"""
    if image_id not in image_store:
        return JSONResponse(status_code=404, content={"error": "Image not found"})
    
    # This would run the entire pipeline in sequence
    # For a real implementation, you might want to use background tasks
    background_tasks.add_task(process_all_steps, image_id, request)
    
    return ProcessResponse(
        image_id=image_id,
        blocks=[],
        status="processing_started"
    )

async def process_all_steps(image_id: str, request: TranslationRequest):
    # Implementation of the full pipeline
    # This would call each step in sequence
    pass

# Add router to app
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)