import cv2
import numpy as np
from typing import List, Dict, Any, Tuple

# Curated vibrant colors for object IDs (RGB / BGR)
COLOR_PALETTE = [
    (0, 240, 255),    # Electric Cyan
    (255, 0, 128),    # Neon Magenta
    (0, 255, 128),    # Neon Mint
    (255, 180, 0),    # Bright Amber
    (140, 0, 255),    # Electric Violet
    (255, 60, 60),    # Coral Red
    (0, 180, 255),    # Sky Blue
    (255, 230, 0),    # Neon Yellow
    (0, 255, 200),    # Turquoise
    (255, 100, 200),  # Pink
]

def get_color_for_id(object_id: int) -> Tuple[int, int, int]:
    """Generates consistent BGR color based on object ID hash."""
    color_rgb = COLOR_PALETTE[object_id % len(COLOR_PALETTE)]
    return (color_rgb[2], color_rgb[1], color_rgb[0])  # Convert RGB to OpenCV BGR

def draw_rounded_rectangle(img: np.ndarray, pt1: Tuple[int, int], pt2: Tuple[int, int], color: Tuple[int, int, int], thickness: int = 2, radius: int = 8):
    """Draws a rectangle with rounded corners."""
    x1, y1 = pt1
    x2, y2 = pt2

    # Corner arcs
    cv2.ellipse(img, (x1 + radius, y1 + radius), (radius, radius), 180, 0, 90, color, thickness)
    cv2.ellipse(img, (x2 - radius, y1 + radius), (radius, radius), 270, 0, 90, color, thickness)
    cv2.ellipse(img, (x1 + radius, y2 - radius), (radius, radius), 90, 0, 90, color, thickness)
    cv2.ellipse(img, (x2 - radius, y2 - radius), (radius, radius), 0, 0, 90, color, thickness)

    # Edge lines
    cv2.line(img, (x1 + radius, y1), (x2 - radius, y1), color, thickness)
    cv2.line(img, (x1 + radius, y2), (x2 - radius, y2), color, thickness)
    cv2.line(img, (x1, y1 + radius), (x1, y2 - radius), color, thickness)
    cv2.line(img, (x2, y1 + radius), (x2, y2 - radius), color, thickness)

def annotate_frame(frame: np.ndarray, tracked_objects: List[Dict[str, Any]], fps: float = 0.0) -> np.ndarray:
    """
    Annotates video frame with rounded bounding boxes, class chips, ID badges, and telemetry overlay.
    """
    annotated = frame.copy()
    
    for obj in tracked_objects:
        obj_id = obj['id']
        bbox = obj['bbox']
        cls_name = obj['class_name']
        conf = obj['confidence']
        
        x1, y1, x2, y2 = [int(round(c)) for c in bbox]
        color = get_color_for_id(obj_id)

        # Draw semi-transparent fill for bounding box
        overlay = annotated.copy()
        cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
        cv2.addWeighted(overlay, 0.08, annotated, 0.92, 0, annotated)

        # Draw rounded box border
        draw_rounded_rectangle(annotated, (x1, y1), (x2, y2), color, thickness=2, radius=6)

        # Label texts
        id_str = f"ID #{obj_id}"
        meta_str = f"{cls_name.upper()} {int(conf * 100)}%"

        # Calculate text sizes
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.45
        font_thick = 1

        (id_w, id_h), _ = cv2.getTextSize(id_str, font, font_scale, font_thick)
        (meta_w, meta_h), _ = cv2.getTextSize(meta_str, font, font_scale, font_thick)

        chip_h = max(id_h, meta_h) + 10
        chip_w = id_w + meta_w + 24

        # Chip background position
        chip_x1 = x1
        chip_y1 = max(0, y1 - chip_h - 4)
        chip_x2 = chip_x1 + chip_w
        chip_y2 = chip_y1 + chip_h

        # Draw dark glass chip background
        cv2.rectangle(annotated, (chip_x1, chip_y1), (chip_x2, chip_y2), (15, 20, 28), -1)
        cv2.rectangle(annotated, (chip_x1, chip_y1), (chip_x2, chip_y2), color, 1)

        # Draw ID badge inside chip
        badge_w = id_w + 10
        cv2.rectangle(annotated, (chip_x1 + 2, chip_y1 + 2), (chip_x1 + badge_w, chip_y2 - 2), color, -1)
        
        # ID Text (dark on color badge)
        cv2.putText(annotated, id_str, (chip_x1 + 6, chip_y1 + chip_h - 6), font, font_scale, (10, 14, 20), font_thick + 1, cv2.LINE_AA)
        
        # Class + Conf Text (white on dark background)
        cv2.putText(annotated, meta_str, (chip_x1 + badge_w + 8, chip_y1 + chip_h - 6), font, font_scale, (240, 240, 245), font_thick, cv2.LINE_AA)

    # Top-Left Telemetry Overlay on video frame
    if fps > 0:
        telemetry_str = f"LIVE | FPS: {round(fps, 1)} | OBJECTS: {len(tracked_objects)}"
        cv2.rectangle(annotated, (10, 10), (270, 36), (10, 14, 20), -1)
        cv2.rectangle(annotated, (10, 10), (270, 36), (0, 240, 255), 1)
        cv2.circle(annotated, (25, 23), 4, (0, 255, 128), -1)
        cv2.putText(annotated, telemetry_str, (36, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (220, 230, 240), 1, cv2.LINE_AA)

    return annotated
