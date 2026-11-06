import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.api.routes import router as api_router
from app.api.websocket import router as ws_router

app = FastAPI(
    title=settings.APP_NAME,
    description="Real-Time Object Detection and Multi-Object Tracking API (YOLOv8 + SORT / Deep SORT)",
    version="1.0.0"
)

# CORS middleware for React Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include REST & WebSocket API Routers
app.include_router(api_router)
app.include_router(ws_router)

# Serve uploaded videos statically
if os.path.exists(settings.UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

@app.get("/")
def read_root():
    return {
        "status": "online",
        "app": settings.APP_NAME,
        "docs": "/docs",
        "websocket": "/ws/stream"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
