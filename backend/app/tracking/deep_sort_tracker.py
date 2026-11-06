import torch
import torch.nn as nn
import torchvision.transforms as transforms
import torchvision.models as models
import numpy as np
import cv2
from typing import List, Dict, Any, Tuple
from scipy.optimize import linear_sum_assignment
from app.tracking.sort_tracker import KalmanBoxTracker, iou_batch

class FeatureExtractor(nn.Module):
    def __init__(self):
        super().__init__()
        # Use lightweight MobileNetV3 for fast CPU feature extraction
        mobilenet = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.DEFAULT)
        self.features = mobilenet.features
        self.pool = nn.AdaptiveAvgPool2d((1, 1))

    def forward(self, x):
        x = self.features(x)
        x = self.pool(x)
        x = x.view(x.size(0), -1)
        # Normalize embeddings to unit length (for cosine distance)
        norm = torch.norm(x, p=2, dim=1, keepdim=True)
        norm = torch.where(norm == 0, torch.ones_like(norm), norm)
        return x / norm

class DeepSortTracker:
    def __init__(self, max_age: int = 30, min_hits: int = 3, iou_threshold: float = 0.3, nn_budget: int = 100):
        self.max_age = max_age
        self.min_hits = min_hits
        self.iou_threshold = iou_threshold
        self.nn_budget = nn_budget
        
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.feature_extractor = FeatureExtractor().to(self.device).eval()
        
        self.transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((128, 64)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

        self.trackers: List[KalmanBoxTracker] = []
        self.features_gallery: Dict[int, List[np.ndarray]] = {}  # id -> list of embeddings
        self.frame_count = 0

    def _extract_features(self, frame: np.ndarray, bboxes: List[List[float]]) -> np.ndarray:
        if len(bboxes) == 0:
            return np.empty((0, 576))

        crops = []
        h_img, w_img = frame.shape[:2]
        
        for bbox in bboxes:
            x1, y1, x2, y2 = [int(round(c)) for c in bbox]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w_img, x2), min(h_img, y2)
            
            if x2 <= x1 or y2 <= y1:
                # Fallback tiny blank crop
                crop = np.zeros((64, 32, 3), dtype=np.uint8)
            else:
                crop = frame[y1:y2, x1:x2]
                crop = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
            
            tensor_crop = self.transform(crop)
            crops.append(tensor_crop)

        batch = torch.stack(crops).to(self.device)
        with torch.no_grad():
            embeddings = self.feature_extractor(batch).cpu().numpy()

        return embeddings

    def update(self, frame: np.ndarray, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        self.frame_count += 1

        # Extract appearance features for current detections
        bboxes = [d['bbox'] for d in detections]
        det_features = self._extract_features(frame, bboxes)

        # Predict Kalman states
        trks = np.zeros((len(self.trackers), 4))
        to_del = []
        for t, trk in enumerate(self.trackers):
            pos = trk.predict()[0]
            trks[t] = [pos[0], pos[1], pos[2], pos[3]]
            if np.any(np.isnan(pos)):
                to_del.append(t)

        for t in reversed(to_del):
            self.trackers.pop(t)
            trks = np.delete(trks, t, axis=0)

        dets = np.array(bboxes) if len(bboxes) > 0 else np.zeros((0, 4))

        # Match using appearance cosine distance + IOU
        matched, unmatched_dets, unmatched_trks = self._associate(dets, trks, det_features)

        # Update matched trackers
        for m in matched:
            det_idx, trk_idx = m[0], m[1]
            det = detections[det_idx]
            trk = self.trackers[trk_idx]
            
            trk.update(
                np.array(det['bbox']),
                det['class_id'],
                det['class_name'],
                det['confidence']
            )
            
            # Save feature embedding to gallery
            if len(det_features) > det_idx:
                feat = det_features[det_idx]
                if trk.id not in self.features_gallery:
                    self.features_gallery[trk.id] = []
                self.features_gallery[trk.id].append(feat)
                if len(self.features_gallery[trk.id]) > self.nn_budget:
                    self.features_gallery[trk.id].pop(0)

        # Create new trackers
        for i in unmatched_dets:
            det = detections[i]
            trk = KalmanBoxTracker(
                np.array(det['bbox']),
                det['class_id'],
                det['class_name'],
                det['confidence']
            )
            self.trackers.append(trk)
            if len(det_features) > i:
                self.features_gallery[trk.id] = [det_features[i]]

        # Output active tracks
        ret = []
        i = len(self.trackers)
        for trk in reversed(self.trackers):
            d = trk.get_state()
            if (trk.time_since_update < 1) and (trk.hit_streak >= self.min_hits or self.frame_count <= self.min_hits):
                ret.append({
                    "id": trk.id,
                    "bbox": [round(float(c), 2) for c in d],
                    "class_id": trk.class_id,
                    "class_name": trk.class_name,
                    "confidence": trk.confidence,
                    "duration_frames": trk.age
                })
            i -= 1
            if trk.time_since_update > self.max_age:
                self.trackers.pop(i)
                if trk.id in self.features_gallery:
                    del self.features_gallery[trk.id]

        return ret

    def _associate(self, detections: np.ndarray, trackers: np.ndarray, det_features: np.ndarray):
        if len(trackers) == 0:
            return np.empty((0, 2), dtype=int), np.arange(len(detections)), np.empty((0,), dtype=int)
        if len(detections) == 0:
            return np.empty((0, 2), dtype=int), np.empty((0,), dtype=int), np.arange(len(trackers))

        # Calculate cosine distance matrix between det_features and tracker galleries
        dist_matrix = np.ones((len(detections), len(trackers)))
        for t_idx, trk in enumerate(self.trackers):
            if trk.id in self.features_gallery and len(self.features_gallery[trk.id]) > 0:
                trk_feats = np.array(self.features_gallery[trk.id])  # (K, 576)
                # Compute cosine distance (1 - cosine similarity)
                cos_sim = np.dot(det_features, trk_feats.T)  # (N, K)
                min_dists = 1.0 - np.max(cos_sim, axis=1)  # minimum distance to gallery
                dist_matrix[:, t_idx] = min_dists

        # Also calculate IOU matrix
        iou_matrix = iou_batch(detections, trackers)
        
        # Combine distance: cost = 0.7 * cosine_dist + 0.3 * (1 - IOU)
        cost_matrix = 0.7 * dist_matrix + 0.3 * (1.0 - iou_matrix)

        row_ind, col_ind = linear_sum_assignment(cost_matrix)
        matched_indices = np.asarray(list(zip(row_ind, col_ind)))

        unmatched_dets = []
        for d in range(len(detections)):
            if d not in matched_indices[:, 0]:
                unmatched_dets.append(d)

        unmatched_trks = []
        for t in range(len(trackers)):
            if t not in matched_indices[:, 1]:
                unmatched_trks.append(t)

        matches = []
        for m in matched_indices:
            # Gating threshold: cost < 0.6 and IOU > 0.1
            if cost_matrix[m[0], m[1]] > 0.6 or iou_matrix[m[0], m[1]] < 0.1:
                unmatched_dets.append(m[0])
                unmatched_trks.append(m[1])
            else:
                matches.append(m.reshape(1, 2))

        if len(matches) == 0:
            matches = np.empty((0, 2), dtype=int)
        else:
            matches = np.concatenate(matches, axis=0)

        return matches, np.array(unmatched_dets), np.array(unmatched_trks)
