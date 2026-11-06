import cv2
import numpy as np
import base64
import time
import os
from typing import Generator, Tuple, Optional

def decode_image_from_bytes(image_bytes: bytes) -> Optional[np.ndarray]:
    """Decodes binary JPEG bytes into an OpenCV BGR image."""
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return frame
    except Exception:
        return None

def encode_image_to_jpeg_bytes(frame: np.ndarray, quality: int = 85) -> bytes:
    """Encodes an OpenCV image to JPEG bytes."""
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    _, buffer = cv2.imencode('.jpg', frame, encode_param)
    return buffer.tobytes()

def encode_image_to_base64(frame: np.ndarray, quality: int = 80) -> str:
    """Encodes an OpenCV image to base64 data string."""
    jpeg_bytes = encode_image_to_jpeg_bytes(frame, quality)
    b64_str = base64.b64encode(jpeg_bytes).decode('utf-8')
    return f"data:image/jpeg;base64,{b64_str}"

class DemoVideoGenerator:
    """Generates a dynamic realistic synthetic scene with moving objects (vehicles, persons) for instant demo testing."""
    def __init__(self, width: int = 640, height: int = 480):
        self.width = width
        self.height = height
        self.frame_idx = 0
        
        # Simulated moving objects with trajectories
        self.objects = [
            {"id": "demo_car_1", "type": "car", "color": (50, 100, 240), "x": 50, "y": 280, "vx": 3.2, "vy": 0, "w": 110, "h": 55},
            {"id": "demo_car_2", "type": "car", "color": (220, 120, 40), "x": 550, "y": 340, "vx": -4.0, "vy": 0, "w": 130, "h": 65},
            {"id": "demo_person_1", "type": "person", "color": (60, 220, 100), "x": 180, "y": 150, "vx": 1.2, "vy": 0.8, "w": 35, "h": 85},
            {"id": "demo_person_2", "type": "person", "color": (200, 80, 220), "x": 420, "y": 180, "vx": -1.0, "vy": 0.5, "w": 30, "h": 75},
            {"id": "demo_dog_1", "type": "dog", "color": (40, 200, 240), "x": 220, "y": 200, "vx": 1.5, "vy": 0.7, "w": 40, "h": 35},
        ]

    def get_frame(self) -> np.ndarray:
        self.frame_idx += 1
        
        # Dark realistic street road background
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        frame[:] = (20, 26, 35)

        # Draw road & lane markings
        cv2.rectangle(frame, (0, 240), (self.width, self.height), (35, 42, 54), -1)
        lane_dash_offset = (self.frame_idx * 6) % 40
        for x in range(-40 + lane_dash_offset, self.width, 40):
            cv2.line(frame, (x, 310), (x + 20, 310), (200, 210, 225), 2)

        # Draw sidewalk / park top area
        cv2.rectangle(frame, (0, 100), (self.width, 240), (28, 48, 38), -1)

        # Move and render objects
        for obj in self.objects:
            obj["x"] += obj["vx"]
            obj["y"] += obj["vy"]

            # Wrap around boundaries
            if obj["x"] > self.width + 100:
                obj["x"] = -100
            elif obj["x"] < -100:
                obj["x"] = self.width + 100

            if obj["y"] > 220 and obj["type"] == "person":
                obj["vy"] = -abs(obj["vy"])
            elif obj["y"] < 130 and obj["type"] == "person":
                obj["vy"] = abs(obj["vy"])

            x, y, w, h = int(obj["x"]), int(obj["y"]), obj["w"], obj["h"]

            if obj["type"] == "car":
                # Draw vehicle body
                cv2.rectangle(frame, (x, y), (x + w, y + h), obj["color"], -1)
                # Roof
                cv2.rectangle(frame, (x + 15, y - 20), (x + w - 20, y), (200, 220, 240), -1)
                # Wheels
                cv2.circle(frame, (x + 25, y + h), 10, (10, 10, 10), -1)
                cv2.circle(frame, (x + w - 25, y + h), 10, (10, 10, 10), -1)
            elif obj["type"] == "person":
                # Head
                cv2.circle(frame, (x + w // 2, y + 12), 10, obj["color"], -1)
                # Body
                cv2.rectangle(frame, (x + 5, y + 22), (x + w - 5, y + h - 15), obj["color"], -1)
                # Legs
                cv2.line(frame, (x + 10, y + h - 15), (x + 5, y + h), (240, 240, 240), 3)
                cv2.line(frame, (x + w - 10, y + h - 15), (x + w - 5, y + h), (240, 240, 240), 3)
            elif obj["type"] == "dog":
                # Body & head
                cv2.ellipse(frame, (x + w // 2, y + h // 2), (w // 2, h // 2), 0, 0, 360, obj["color"], -1)
                cv2.circle(frame, (x + w, y + 8), 7, obj["color"], -1)

        return frame
