import os
from typing import List

try:
    from pydantic_settings import BaseSettings
except ImportError:
    try:
        from pydantic import BaseSettings
    except ImportError:
        class BaseSettings:
            pass

class Settings:
    APP_NAME: str = "Real-Time Vision AI - Object Detection & Tracking"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Model defaults
    DEFAULT_MODEL: str = "yolov8n"
    AVAILABLE_MODELS: List[str] = ["yolov8n", "yolov8s", "yolov8m", "faster_rcnn"]
    
    # Tracker defaults
    DEFAULT_TRACKER: str = "sort"
    AVAILABLE_TRACKERS: List[str] = ["sort", "deep_sort"]
    
    # Detection defaults
    DEFAULT_CONF_THRESHOLD: float = 0.35
    DEFAULT_IOU_THRESHOLD: float = 0.45
    
    # Processing defaults
    DEFAULT_FRAME_SKIP: int = 1  # 1 = process every frame, 2 = every 2nd frame
    TARGET_WIDTH: int = 640
    TARGET_HEIGHT: int = 480
    
    # Storage
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
    DEMO_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "demo")

settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.DEMO_DIR, exist_ok=True)

