import time
import torch
import numpy as np
import cv2
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

# COCO 80 classes mapping
COCO_CLASSES = [
    'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light',
    'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow',
    'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
    'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard',
    'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
    'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
    'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone',
    'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear',
    'hair drier', 'toothbrush'
]

class ObjectDetector:
    def __init__(self, default_model: str = "yolov8n"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.current_model_name = ""
        self.model = None
        self.coco_names = COCO_CLASSES
        self.load_model(default_model)

    def load_model(self, model_name: str):
        if self.current_model_name == model_name and self.model is not None:
            return

        logger.info(f"Loading model: {model_name} on device: {self.device}")
        start_t = time.time()
        
        try:
            if model_name.startswith("yolov8"):
                from ultralytics import YOLO
                model_file = f"{model_name}.pt"
                self.model = YOLO(model_file)
                self.current_model_name = model_name
            elif model_name == "faster_rcnn":
                import torchvision
                from torchvision.models.detection import fasterrcnn_resnet50_fpn_v2, FasterRCNN_ResNet50_FPN_V2_Weights
                weights = FasterRCNN_ResNet50_FPN_V2_Weights.DEFAULT
                self.model = fasterrcnn_resnet50_fpn_v2(weights=weights).to(self.device)
                self.model.eval()
                self.coco_names = weights.meta["categories"]
                self.current_model_name = model_name
            else:
                from ultralytics import YOLO
                self.model = YOLO("yolov8n.pt")
                self.current_model_name = "yolov8n"
            
            logger.info(f"Loaded {self.current_model_name} in {time.time() - start_t:.2f}s")
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}. Falling back to YOLOv8n")
            from ultralytics import YOLO
            self.model = YOLO("yolov8n.pt")
            self.current_model_name = "yolov8n"

    def detect(self, frame: np.ndarray, conf_threshold: float = 0.35) -> Tuple[List[Dict[str, Any]], float]:
        """
        Runs object detection on a single frame.
        Returns:
            detections: List of dicts with 'bbox' [x1, y1, x2, y2], 'confidence', 'class_id', 'class_name'
            inference_time_ms: float
        """
        if self.model is None:
            return [], 0.0

        start_t = time.time()
        detections = []

        if self.current_model_name.startswith("yolov8"):
            results = self.model.predict(frame, conf=conf_threshold, device=self.device, verbose=False)[0]
            boxes = results.boxes
            for box in boxes:
                xyxy = box.xyxy[0].cpu().numpy().tolist()
                conf = float(box.conf[0].cpu().numpy())
                cls_id = int(box.cls[0].cpu().numpy())
                cls_name = self.coco_names[cls_id] if cls_id < len(self.coco_names) else f"class_{cls_id}"
                
                detections.append({
                    "bbox": [round(c, 2) for c in xyxy],  # [x1, y1, x2, y2]
                    "confidence": round(conf, 3),
                    "class_id": cls_id,
                    "class_name": cls_name
                })
        elif self.current_model_name == "faster_rcnn":
            # Convert frame BGR -> RGB Tensor
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_tensor = torch.from_numpy(rgb_frame).permute(2, 0, 1).float() / 255.0
            img_tensor = img_tensor.unsqueeze(0).to(self.device)

            with torch.no_grad():
                predictions = self.model(img_tensor)[0]

            boxes = predictions['boxes'].cpu().numpy()
            scores = predictions['scores'].cpu().numpy()
            labels = predictions['labels'].cpu().numpy()

            for box, score, label in zip(boxes, scores, labels):
                if score >= conf_threshold:
                    cls_id = int(label)
                    cls_name = self.coco_names[cls_id] if cls_id < len(self.coco_names) else f"class_{cls_id}"
                    detections.append({
                        "bbox": [round(c, 2) for c in box.tolist()],
                        "confidence": round(float(score), 3),
                        "class_id": cls_id,
                        "class_name": cls_name
                    })

        inference_time_ms = round((time.time() - start_t) * 1000, 2)
        return detections, inference_time_ms

# Global detector instance singleton
detector_instance = ObjectDetector()
