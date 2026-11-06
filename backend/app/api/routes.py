import os
import shutil
import uuid
import torch
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.models.detector import detector_instance

router = APIRouter(prefix="/api", tags=["API"])

@router.get("/config")
def get_config():
    """Returns available models, trackers, and system configuration."""
    return {
        "models": [
            {"id": "yolov8n", "name": "YOLOv8 Nano (Fastest)", "speed": "Ultra Fast", "accuracy": "Good"},
            {"id": "yolov8s", "name": "YOLOv8 Small (Balanced)", "speed": "Fast", "accuracy": "High"},
            {"id": "yolov8m", "name": "YOLOv8 Medium (Accurate)", "speed": "Medium", "accuracy": "Very High"},
            {"id": "faster_rcnn", "name": "Faster R-CNN (ResNet50)", "speed": "Slower (CPU)", "accuracy": "High Precision"},
        ],
        "trackers": [
            {"id": "sort", "name": "SORT (Kalman + Hungarian)", "description": "High-speed real-time IOU tracking"},
            {"id": "deep_sort", "name": "Deep SORT (Appearance Embeddings)", "description": "Deep appearance matching for crowded/occluded scenes"}
        ],
        "default_model": settings.DEFAULT_MODEL,
        "default_tracker": settings.DEFAULT_TRACKER,
        "default_confidence": settings.DEFAULT_CONF_THRESHOLD,
        "default_frame_skip": settings.DEFAULT_FRAME_SKIP,
        "device": "CUDA (GPU)" if torch.cuda.is_available() else "CPU"
    }

@router.get("/status")
def get_status():
    """Returns current device status and active detector model."""
    return {
        "status": "online",
        "current_model": detector_instance.current_model_name,
        "device": detector_instance.device,
        "cuda_available": torch.cuda.is_available()
    }

@router.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """Handles video file upload (MP4, AVI, MOV, MKV, WEBM)."""
    allowed_extensions = [".mp4", ".avi", ".mov", ".mkv", ".webm"]
    ext = os.path.splitext(file.filename)[1].lower()
    
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file format. Supported: {', '.join(allowed_extensions)}")

    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)

    try:
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {str(e)}")

    return {
        "status": "success",
        "filename": filename,
        "original_name": file.filename,
        "file_url": f"/uploads/{filename}"
    }

@router.get("/videos")
def list_videos():
    """Returns list of uploaded video files."""
    files = []
    if os.path.exists(settings.UPLOAD_DIR):
        for f in os.listdir(settings.UPLOAD_DIR):
            if f.endswith((".mp4", ".avi", ".mov", ".mkv", ".webm")):
                path = os.path.join(settings.UPLOAD_DIR, f)
                files.append({
                    "filename": f,
                    "size_mb": round(os.path.getsize(path) / (1024 * 1024), 2)
                })
    return {"videos": files}
