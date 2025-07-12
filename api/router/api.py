import os
import cv2
import numpy as np
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, Depends
from fastapi.responses import JSONResponse, FileResponse
import uuid
import shutil
from datetime import datetime
from dependency_injector.wiring import inject, Provide
from controller.api_pipeline_controller import APIPipelineController
from data_model.request import ProcessResponse, TranslationRequest, TextBlockData
from container.app_container import AppContainer


router = APIRouter(prefix="/api/v1", tags=["translation"])


image_store = {}


@router.post("/upload", response_model=ProcessResponse)
@inject
async def upload_image(
    file: UploadFile = File(...),
    source_language: str = Form(...),
    target_language: str = Form(...),
    storage_config: dict = Depends(Provide[AppContainer.storage_config]),
):
    # Generate unique ID for this image
    image_id = str(uuid.uuid4())

    # Save uploaded file
    ext = os.path.splitext(file.filename or "")[1]
    file_path = os.path.join(storage_config["results_dir"], f"{image_id}{ext}")
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Store image info
    image_store[image_id] = {
        "path": file_path,
        "source_language": source_language,
        "target_language": target_language,
        "status": "uploaded",
    }

    return ProcessResponse(image_id=image_id, blocks=[], status="uploaded")


@router.post("/detect-blocks/{image_id}", response_model=ProcessResponse)
@inject
async def detect_blocks(
    image_id: str,
    pipeline: APIPipelineController = Depends(Provide[AppContainer.api_pipeline]),
):
    if image_id not in image_store:
        return JSONResponse(status_code=404, content={"error": "Image not found"})

    # Load image
    image_path = image_store[image_id]["path"]
    image = cv2.imread(image_path)

    # Detect blocks
    blk_list = pipeline.detect_blocks(image)

    # Convert blocks to response format
    blocks = []
    for i, blk in enumerate(blk_list):
        blocks.append(
            TextBlockData(
                id=f"{i}",
                xyxy=(
                    blk.xyxy.tolist() if hasattr(blk.xyxy, "tolist") else list(blk.xyxy)
                ),
                angle=blk.angle,
            )
        )

    # Update image store
    image_store[image_id]["blocks"] = blk_list
    image_store[image_id]["status"] = "blocks_detected"

    return ProcessResponse(image_id=image_id, blocks=blocks, status="blocks_detected")


@router.post("/ocr/{image_id}", response_model=ProcessResponse)
@inject
async def ocr_image(
    image_id: str,
    pipeline: APIPipelineController = Depends(Provide[AppContainer.api_pipeline]),
):
    if image_id not in image_store:
        return JSONResponse(status_code=404, content={"error": "Image not found"})

    if "blocks" not in image_store[image_id]:
        return JSONResponse(
            status_code=400, content={"error": "Blocks not detected yet"}
        )

    # Load image and blocks
    image_path = image_store[image_id]["path"]
    image = cv2.imread(image_path)
    blk_list = image_store[image_id]["blocks"]
    source_lang = image_store[image_id]["source_language"]

    # Process OCR
    blk_list = pipeline.process_ocr(image, blk_list, source_lang)

    # Convert blocks to response format
    blocks = []
    for i, blk in enumerate(blk_list):
        xyxy = list(blk.xyxy)
        blocks.append(
            TextBlockData(id=f"{i}", xyxy=xyxy, text=blk.text, angle=blk.angle)
        )

    # Update image store
    image_store[image_id]["blocks"] = blk_list
    image_store[image_id]["status"] = "ocr_completed"

    return ProcessResponse(image_id=image_id, blocks=blocks, status="ocr_completed")


@router.post("/translate/{image_id}", response_model=ProcessResponse)
@inject
async def translate_image(
    image_id: str,
    request: TranslationRequest,
    pipeline: APIPipelineController = Depends(Provide[AppContainer.api_pipeline]),
):
    if image_id not in image_store:
        return JSONResponse(status_code=404, content={"error": "Image not found"})

    if "blocks" not in image_store[image_id]:
        return JSONResponse(
            status_code=400, content={"error": "Blocks not detected yet"}
        )

    # Load image and blocks
    image_path = image_store[image_id]["path"]
    image = cv2.imread(image_path)
    blk_list = image_store[image_id]["blocks"]
    source_lang = image_store[image_id]["source_language"]
    target_lang = image_store[image_id]["target_language"]

    # Translate
    blk_list = pipeline.translate_blocks(
        blk_list, image, source_lang, target_lang, request.extra_context or ""
    )

    # Convert blocks to response format
    blocks = []
    for i, blk in enumerate(blk_list):
        xyxy_list = blk.xyxy.tolist() if hasattr(blk.xyxy, "tolist") else list(blk.xyxy)
        blocks.append(
            TextBlockData(
                id=f"{i}",
                xyxy=xyxy_list,
                text=blk.text,
                translation=blk.translation,
                angle=blk.angle,
            )
        )

    # Update image store
    image_store[image_id]["blocks"] = blk_list
    image_store[image_id]["status"] = "translated"

    return ProcessResponse(image_id=image_id, blocks=blocks, status="translated")


@router.post("/inpaint/{image_id}")
@inject
async def inpaint_image(
    image_id: str,
    background_tasks: BackgroundTasks,
    request: TranslationRequest,
    pipeline: APIPipelineController = Depends(Provide[AppContainer.api_pipeline]),
    storage_config: dict = Depends(Provide[AppContainer.storage_config]),
):
    if image_id not in image_store:
        return JSONResponse(status_code=404, content={"error": "Image not found"})

    if "blocks" not in image_store[image_id]:
        return JSONResponse(
            status_code=400, content={"error": "Blocks not detected yet"}
        )

    # Load image and blocks
    image_path = image_store[image_id]["path"]
    image = cv2.imread(image_path)
    blk_list = image_store[image_id]["blocks"]

    # Inpaint
    inpainted_image = pipeline.inpaint_image(image, blk_list, request.use_gpu)

    # Save inpainted image
    result_path = os.path.join(
        storage_config["results_dir"], f"{image_id}_inpainted.jpg"
    )
    cv2.imwrite(result_path, inpainted_image)

    # Update image store
    image_store[image_id]["inpainted_path"] = result_path
    image_store[image_id]["status"] = "inpainted"

    return {"image_id": image_id, "status": "inpainted", "result_path": result_path}


@router.post("/render/{image_id}")
@inject
async def render_translated_image(
    image_id: str,
    pipeline: APIPipelineController = Depends(Provide[AppContainer.api_pipeline]),
    storage_config: dict = Depends(Provide[AppContainer.storage_config]),
):
    if image_id not in image_store:
        return JSONResponse(status_code=404, content={"error": "Image not found"})

    if "inpainted_path" not in image_store[image_id]:
        return JSONResponse(
            status_code=400, content={"error": "Image not inpainted yet"}
        )

    # Load inpainted image
    inpainted_path = image_store[image_id]["inpainted_path"]
    inpainted_image = cv2.imread(inpainted_path)

    # Get blocks
    blk_list = image_store[image_id]["blocks"]

    # Render text on image
    final_image = pipeline.render_text(inpainted_image, blk_list)

    # Save rendered image
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_path = os.path.join(
        storage_config["results_dir"], f"{image_id}_translated_{timestamp}.jpg"
    )
    cv2.imwrite(result_path, final_image)

    # Update image store
    image_store[image_id]["rendered_path"] = result_path
    image_store[image_id]["status"] = "rendered"

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
        return JSONResponse(
            status_code=400,
            content={"error": f"No result available. Current status: {status}"},
        )


@router.post("/translate-all/{image_id}", response_model=ProcessResponse)
@inject
async def translate_all_steps(
    image_id: str,
    request: TranslationRequest,
    background_tasks: BackgroundTasks,
    pipeline: APIPipelineController = Depends(Provide[AppContainer.api_pipeline]),
):
    """Process all steps at once: detect blocks, OCR, translate, inpaint, and render"""
    if image_id not in image_store:
        return JSONResponse(status_code=404, content={"error": "Image not found"})

    # Load image
    image_path = image_store[image_id]["path"]
    image = cv2.imread(image_path)
    source_lang = image_store[image_id]["source_language"]
    target_lang = image_store[image_id]["target_language"]

    # Process full pipeline
    background_tasks.add_task(
        process_all_steps, image_id, request, image, source_lang, target_lang, pipeline
    )

    return ProcessResponse(image_id=image_id, blocks=[], status="processing_started")


async def process_all_steps(
    image_id: str,
    request: TranslationRequest,
    image: np.ndarray,
    source_lang: str,
    target_lang: str,
    pipeline: APIPipelineController,
    storage_config: dict = Depends(Provide[AppContainer.storage_config]),
):
    """Implementation of the full pipeline"""
    try:
        # Process full pipeline
        result = pipeline.process_full_pipeline(
            image,
            source_lang,
            target_lang,
            request.extra_context or "",
            request.use_gpu,
        )

        # Save final image
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_path = os.path.join(
            storage_config["results_dir"], f"{image_id}_final_{timestamp}.jpg"
        )
        cv2.imwrite(result_path, result["final_image"])

        # Update image store
        image_store[image_id]["final_path"] = result_path
        image_store[image_id]["status"] = "completed"
        image_store[image_id]["blocks"] = result["text_blocks"]

    except Exception as e:
        image_store[image_id]["status"] = "error"
        image_store[image_id]["error"] = str(e)
        print(f"Error processing image {image_id}: {e}")
