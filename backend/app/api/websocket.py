import json
import asyncio
import time
import os
import cv2
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging

from app.core.config import settings
from app.models.detector import detector_instance
from app.tracking.sort_tracker import SortTracker
from app.tracking.deep_sort_tracker import DeepSortTracker
from app.utils.visualizer import annotate_frame
from app.utils.video import (
    decode_image_from_bytes,
    encode_image_to_base64,
    DemoVideoGenerator
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])

class StreamSession:
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.source = "demo"  # "demo", "webcam", "file"
        self.filename = ""
        self.model_name = settings.DEFAULT_MODEL
        self.tracker_type = settings.DEFAULT_TRACKER
        self.conf_threshold = settings.DEFAULT_CONF_THRESHOLD
        self.frame_skip = settings.DEFAULT_FRAME_SKIP
        
        self.tracker = SortTracker()
        self.is_running = False
        self.is_paused = False
        self.frame_idx = 0
        self.stream_task = None
        
        self.fps = 0.0
        self.last_time = time.time()
        self.detected_class_counts = {}
        self.total_objects_counter = 0
        self.seen_object_ids = set()

    def cancel_stream_task(self):
        if self.stream_task and not self.stream_task.done():
            self.stream_task.cancel()
            self.stream_task = None

    def update_config(self, config_data: dict):
        if "model" in config_data and config_data["model"] != self.model_name:
            self.model_name = config_data["model"]
            detector_instance.load_model(self.model_name)

        if "tracker" in config_data and config_data["tracker"] != self.tracker_type:
            self.tracker_type = config_data["tracker"]
            if self.tracker_type == "sort":
                self.tracker = SortTracker()
            elif self.tracker_type == "deep_sort":
                self.tracker = DeepSortTracker()

        if "confidence" in config_data:
            self.conf_threshold = float(config_data["confidence"])

        if "frame_skip" in config_data:
            self.frame_skip = max(1, int(config_data["frame_skip"]))

    def process_frame(self, frame: np.ndarray) -> tuple[np.ndarray, list, dict]:
        """Runs detection, tracking, visualizer, and telemetry updates on frame."""
        self.frame_idx += 1
        
        # Calculate FPS
        now = time.time()
        delta = now - self.last_time
        if delta > 0:
            current_fps = 1.0 / delta
            self.fps = round(0.8 * self.fps + 0.2 * current_fps, 1)  # Smooth FPS
        self.last_time = now

        # Run Object Detector (or skip frame for CPU optimization)
        if self.frame_idx % self.frame_skip == 0:
            detections, inf_time = detector_instance.detect(frame, self.conf_threshold)
        else:
            detections = []
            inf_time = 0.0

        # Run Tracker
        if self.tracker_type == "deep_sort" and isinstance(self.tracker, DeepSortTracker):
            tracked_objects = self.tracker.update(frame, detections)
        else:
            tracked_objects = self.tracker.update(detections)

        # Update telemetry statistics
        current_class_counts = {}
        for obj in tracked_objects:
            obj_id = obj["id"]
            cls_name = obj["class_name"]
            
            if obj_id not in self.seen_object_ids:
                self.seen_object_ids.add(obj_id)
                self.total_objects_counter += 1

            current_class_counts[cls_name] = current_class_counts.get(cls_name, 0) + 1

        # Draw frame annotations
        annotated = annotate_frame(frame, tracked_objects, fps=self.fps)

        telemetry = {
            "fps": self.fps,
            "inference_time_ms": inf_time,
            "active_tracks_count": len(tracked_objects),
            "total_objects_count": self.total_objects_counter,
            "class_counts": current_class_counts,
            "frame_index": self.frame_idx,
            "model": self.model_name,
            "tracker": self.tracker_type
        }

        return annotated, tracked_objects, telemetry

@router.websocket("/ws/stream")
async def websocket_stream_endpoint(websocket: WebSocket):
    await websocket.accept()
    session = StreamSession(websocket)
    logger.info("WebSocket client connected")

    try:
        while True:
            # Handle incoming WebSocket message (either JSON control command or Binary webcam frame)
            message = await websocket.receive()

            if message.get("type") == "websocket.disconnect":
                logger.info("WebSocket disconnect message received")
                break

            if "text" in message:
                try:
                    data = json.loads(message["text"])
                    msg_type = data.get("type", "")

                    if msg_type == "config":
                        session.update_config(data)
                        await websocket.send_text(json.dumps({
                            "type": "ack",
                            "status": "config_updated",
                            "model": session.model_name,
                            "tracker": session.tracker_type,
                            "confidence": session.conf_threshold
                        }))

                    elif msg_type == "start":
                        session.cancel_stream_task()
                        session.source = data.get("source", "demo")
                        session.filename = data.get("filename", "")
                        session.is_running = True
                        session.is_paused = False

                        if session.source in ["demo", "file"]:
                            session.stream_task = asyncio.create_task(run_file_or_demo_stream(session))

                    elif msg_type == "pause":
                        session.is_paused = not session.is_paused

                    elif msg_type == "stop":
                        session.is_running = False
                        session.cancel_stream_task()

                except Exception as e:
                    logger.error(f"Error handling JSON text message: {e}")

            elif "bytes" in message and session.source == "webcam" and session.is_running and not session.is_paused:
                # Direct webcam binary JPEG frame processing
                image_bytes = message["bytes"]
                frame = decode_image_from_bytes(image_bytes)

                if frame is not None:
                    annotated, tracked_objects, telemetry = session.process_frame(frame)
                    b64_frame = encode_image_to_base64(annotated, quality=80)

                    response_payload = {
                        "type": "frame",
                        "image": b64_frame,
                        "objects": tracked_objects,
                        "telemetry": telemetry
                    }
                    await websocket.send_text(json.dumps(response_payload))

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket session error: {e}")
    finally:
        session.is_running = False
        session.cancel_stream_task()

async def run_file_or_demo_stream(session: StreamSession):
    """Background task for video file or synthetic demo playback streaming."""
    cap = None
    demo_gen = None

    if session.source == "demo":
        demo_gen = DemoVideoGenerator(width=640, height=480)
    elif session.source == "file" and session.filename:
        video_path = os.path.join(settings.UPLOAD_DIR, session.filename)
        if os.path.exists(video_path):
            cap = cv2.VideoCapture(video_path)

    target_fps = 25.0
    frame_delay = 1.0 / target_fps

    while session.is_running:
        if session.is_paused:
            await asyncio.sleep(0.1)
            continue

        frame = None

        if session.source == "demo" and demo_gen:
            frame = demo_gen.get_frame()
        elif session.source == "file" and cap:
            ret, read_frame = cap.read()
            if not ret:
                # Loop video when reaching the end
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, read_frame = cap.read()
            if ret:
                # Resize large videos for performance
                h, w = read_frame.shape[:2]
                if w > 640:
                    scale = 640 / w
                    read_frame = cv2.resize(read_frame, (640, int(h * scale)))
                frame = read_frame

        if frame is not None:
            annotated, tracked_objects, telemetry = session.process_frame(frame)
            b64_frame = encode_image_to_base64(annotated, quality=80)

            response_payload = {
                "type": "frame",
                "image": b64_frame,
                "objects": tracked_objects,
                "telemetry": telemetry
            }

            try:
                await session.websocket.send_text(json.dumps(response_payload))
            except Exception:
                break

        await asyncio.sleep(frame_delay)

    if cap:
        cap.release()
