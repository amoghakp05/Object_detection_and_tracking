# Real-Time Object Detection & Multi-Object Tracking Web Application

A full-stack, production-quality web application built for real-time video object detection and multi-object tracking (SORT / Deep SORT) with a dark-mode glassmorphic telemetry dashboard.

---

## 🏗️ System Architecture

```text
+-----------------------------------------------------------------------------------+
|                                  BROWSER CLIENT                                   |
|  +-----------------------------------------------------------------------------+  |
|  |                             React + Vite Frontend                           |  |
|  |  [Header] [Video Viewport Canvas] [Controls Panel] [Analytics] [Tracked Table]|  |
|  +-----------------------------------------------------------------------------+  |
|                                       ^                                           |
|                   WebSocket Stream / JSON Control Commands                        |
|                                       v                                           |
+-----------------------------------------------------------------------------------+
                                        |
+-----------------------------------------------------------------------------------+
|                                 FASTAPI BACKEND                                   |
|  +------------------------+  +----------------------+  +-----------------------+  |
|  |   WebSocket / REST API |  | Detection Engine     |  | Tracking Engine       |  |
|  | - Stream Endpoint      |  | - YOLOv8 (n/s/m)     |  | - SORT (Kalman+IOU)   |  |
|  | - Upload Handler       |  | - Faster R-CNN       |  | - Deep SORT (Embeds)  |  |
|  +------------------------+  +----------------------+  +-----------------------+  |
|                                       ^                                           |
|                          OpenCV Frame Annotator                                   |
+-----------------------------------------------------------------------------------+
```

---

## ⚡ Key Features

- **Multi-Source Video Input**: Supports browser webcam streams, custom uploaded video files (MP4/AVI/MOV), and synthetic demo video loop.
- **Swappable Detection Models**:
  - `YOLOv8 Nano (yolov8n)`: Ultra-fast real-time inference (30+ FPS).
  - `YOLOv8 Small (yolov8s)`: Balanced speed and accuracy.
  - `YOLOv8 Medium (yolov8m)`: High precision for complex scenes.
  - `Faster R-CNN`: PyTorch ResNet50 benchmark option.
- **Multi-Object Tracking (MOT)**:
  - **SORT**: Pure Python/SciPy implementation combining 2D Kalman Filters and Hungarian algorithm (LAP) for high-speed data association.
  - **Deep SORT**: Enhanced tracker combining appearance feature embeddings (MobileNet/ResNet) and Cosine distance metrics for occlusion resistance.
- **High-Performance Streaming**: Low-latency WebSocket binary frame delivery (<50ms glass-to-glass latency).
- **Dark Glassmorphic UI Dashboard**:
  - Live FPS counter & latency telemetry.
  - Interactive controls for confidence thresholds, model/tracker switching, and frame throttling.
  - Tracked objects table with persistent ID badges, class labels, confidence scores, and time-in-frame.
  - Per-class live distribution bar chart.

---

## 📊 Model Performance Benchmarks

| Model | Tracker | Device | Target Resolution | Expected FPS | Accuracy / mAP |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **YOLOv8n** | **SORT** | CPU | 640x480 | **30 - 45 FPS** | 37.3 mAP |
| **YOLOv8n** | **Deep SORT** | CPU | 640x480 | **20 - 30 FPS** | 37.3 mAP + ReID |
| **YOLOv8s** | **SORT** | CPU | 640x480 | **18 - 25 FPS** | 44.9 mAP |
| **YOLOv8m** | **SORT** | CPU | 640x480 | **10 - 16 FPS** | 50.2 mAP |
| **Faster R-CNN** | **SORT** | CPU | 640x480 | **4 - 8 FPS** | 52.0 mAP |

---

## 🚀 Quick Start & Deployment

### 1. Docker Compose (Single Command Setup)

The easiest way to run the entire application:

```bash
docker-compose up --build
```

- **Frontend Application**: `http://localhost:3000`
- **Backend API Docs**: `http://localhost:8000/docs`

---

### 2. Manual Local Setup

#### Backend (Python + FastAPI)

1. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. Run the backend server:
   ```bash
   python backend/main.py
   ```
   Backend will start at `http://localhost:8000`.

#### Frontend (React + Vite + TypeScript)

1. Navigate to frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run development server:
   ```bash
   npm run dev
   ```
   Frontend will start at `http://localhost:3000`.

---

## 📡 API Reference

### REST Endpoints

- `GET /api/config`: Returns available detection models, trackers, and device status.
- `GET /api/status`: Check current backend engine device (CPU/CUDA) and active model.
- `POST /api/upload`: Upload video file (returns `filename` for streaming).
- `GET /api/videos`: List all uploaded video files.

### WebSocket Protocol (`ws://localhost:8000/ws/stream`)

#### Client -> Server (Control Messages):
```json
{
  "type": "start",
  "source": "demo" // or "webcam", "file"
}
```
```json
{
  "type": "config",
  "model": "yolov8s",
  "tracker": "deep_sort",
  "confidence": 0.45,
  "frame_skip": 1
}
```

#### Server -> Client (Frame Payload):
```json
{
  "type": "frame",
  "image": "data:image/jpeg;base64,...",
  "objects": [
    {
      "id": 1,
      "bbox": [120.5, 80.2, 240.1, 310.4],
      "class_id": 0,
      "class_name": "person",
      "confidence": 0.89,
      "duration_frames": 42
    }
  ],
  "telemetry": {
    "fps": 31.4,
    "inference_time_ms": 14.2,
    "active_tracks_count": 1,
    "total_objects_count": 5
  }
}
```
