import numpy as np
from scipy.optimize import linear_sum_assignment
from typing import List, Dict, Any, Tuple

def iou_batch(bb_test: np.ndarray, bb_gt: np.ndarray) -> np.ndarray:
    """
    Computes IOU between two sets of bounding boxes.
    bb_test: (N, 4) [x1, y1, x2, y2]
    bb_gt: (M, 4) [x1, y1, x2, y2]
    Returns IOU matrix of shape (N, M)
    """
    bb_gt = np.expand_dims(bb_gt, 0)
    bb_test = np.expand_dims(bb_test, 1)

    xx1 = np.maximum(bb_test[..., 0], bb_gt[..., 0])
    yy1 = np.maximum(bb_test[..., 1], bb_gt[..., 1])
    xx2 = np.minimum(bb_test[..., 2], bb_gt[..., 2])
    yy2 = np.minimum(bb_test[..., 3], bb_gt[..., 3])

    w = np.maximum(0., xx2 - xx1)
    h = np.maximum(0., yy2 - yy1)

    wh = w * h
    o = wh / (
        (bb_test[..., 2] - bb_test[..., 0]) * (bb_test[..., 3] - bb_test[..., 1]) +
        (bb_gt[..., 2] - bb_gt[..., 0]) * (bb_gt[..., 3] - bb_gt[..., 1]) - wh
    )
    return o

def convert_bbox_to_z(bbox: np.ndarray) -> np.ndarray:
    """
    Converts [x1, y1, x2, y2] box into [cx, cy, s, r] state vector.
    """
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    cx = bbox[0] + w / 2.0
    cy = bbox[1] + h / 2.0
    s = w * h  # scale / area
    r = w / float(h) if h > 0 else 1.0
    return np.array([cx, cy, s, r]).reshape((4, 1))

def convert_x_to_bbox(x: np.ndarray) -> np.ndarray:
    """
    Converts [cx, cy, s, r] state vector back to [x1, y1, x2, y2].
    """
    w = np.sqrt(x[2] * x[3]) if x[2] * x[3] > 0 else 1.0
    h = x[2] / w if w > 0 else 1.0
    cx = x[0]
    cy = x[1]
    return np.array([cx - w / 2.0, cy - h / 2.0, cx + w / 2.0, cy + h / 2.0]).reshape((1, 4))

class KalmanBoxTracker:
    count = 0

    def __init__(self, bbox: np.ndarray, class_id: int, class_name: str, confidence: float):
        # 7D state vector: [cx, cy, s, r, cx_dot, cy_dot, s_dot]
        self.x = np.zeros((7, 1))
        self.x[:4] = convert_bbox_to_z(bbox)
        
        # State transition matrix F
        self.F = np.eye(7)
        self.F[0, 4] = 1
        self.F[1, 5] = 1
        self.F[2, 6] = 1
        
        # Measurement matrix H
        self.H = np.zeros((4, 7))
        self.H[0, 0] = 1
        self.H[1, 1] = 1
        self.H[2, 2] = 1
        self.H[3, 3] = 1
        
        # Covariance matrices
        self.P = np.eye(7) * 10.0
        self.P[4:, 4:] *= 1000.0  # high uncertainty for initial velocities
        self.Q = np.eye(7)
        self.Q[4:, 4:] *= 0.01
        self.R = np.eye(4) * 1.0

        self.time_since_update = 0
        self.id = KalmanBoxTracker.count
        KalmanBoxTracker.count += 1

        self.history = []
        self.hits = 0
        self.hit_streak = 0
        self.age = 0
        
        self.class_id = class_id
        self.class_name = class_name
        self.confidence = confidence
        self.first_seen_age = 0

    def update(self, bbox: np.ndarray, class_id: int, class_name: str, confidence: float):
        self.time_since_update = 0
        self.history = []
        self.hits += 1
        self.hit_streak += 1
        
        self.class_id = class_id
        self.class_name = class_name
        self.confidence = confidence

        z = convert_bbox_to_z(bbox)
        y = z - np.dot(self.H, self.x)
        S = np.dot(np.dot(self.H, self.P), self.H.T) + self.R
        K = np.dot(np.dot(self.P, self.H.T), np.linalg.inv(S))
        self.x = self.x + np.dot(K, y)
        self.P = self.P - np.dot(np.dot(K, self.H), self.P)

    def predict(self) -> np.ndarray:
        if (self.x[6] + self.x[2]) <= 0:
            self.x[6] = 0.0

        self.x = np.dot(self.F, self.x)
        self.P = np.dot(np.dot(self.F, self.P), self.F.T) + self.Q
        self.age += 1

        if self.time_since_update > 0:
            self.hit_streak = 0
        self.time_since_update += 1

        self.history.append(convert_x_to_bbox(self.x))
        return self.history[-1]

    def get_state(self) -> np.ndarray:
        return convert_x_to_bbox(self.x)[0]

class SortTracker:
    def __init__(self, max_age: int = 15, min_hits: int = 2, iou_threshold: float = 0.3):
        self.max_age = max_age
        self.min_hits = min_hits
        self.iou_threshold = iou_threshold
        self.trackers: List[KalmanBoxTracker] = []
        self.frame_count = 0

    def update(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Input: list of detections [{'bbox': [x1, y1, x2, y2], 'confidence': float, 'class_id': int, 'class_name': str}]
        Output: list of tracked objects [{'id': int, 'bbox': [...], 'class_id': int, 'class_name': str, 'confidence': float, 'duration_frames': int}]
        """
        self.frame_count += 1
        
        # Get predicted locations from existing trackers
        trks = np.zeros((len(self.trackers), 4))
        to_del = []
        for t, trk in enumerate(trks):
            pos = self.trackers[t].predict()[0]
            trk[:] = [pos[0], pos[1], pos[2], pos[3]]
            if np.any(np.isnan(pos)):
                to_del.append(t)

        for t in reversed(to_del):
            self.trackers.pop(t)
            trks = np.delete(trks, t, axis=0)

        dets = np.zeros((len(detections), 4))
        for i, det in enumerate(detections):
            dets[i, :] = det['bbox']

        matched, unmatched_dets, unmatched_trks = self._associate_detections_to_trackers(
            dets, trks, self.iou_threshold
        )

        # Update matched trackers
        for m in matched:
            det = detections[m[0]]
            self.trackers[m[1]].update(
                np.array(det['bbox']),
                det['class_id'],
                det['class_name'],
                det['confidence']
            )

        # Create new trackers for unmatched detections
        for i in unmatched_dets:
            det = detections[i]
            trk = KalmanBoxTracker(
                np.array(det['bbox']),
                det['class_id'],
                det['class_name'],
                det['confidence']
            )
            self.trackers.append(trk)

        # Build output list of active tracklets
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
            # Remove dead trackers
            if trk.time_since_update > self.max_age:
                self.trackers.pop(i)

        return ret

    def _associate_detections_to_trackers(self, detections: np.ndarray, trackers: np.ndarray, iou_threshold: float):
        if len(trackers) == 0:
            return np.empty((0, 2), dtype=int), np.arange(len(detections)), np.empty((0,), dtype=int)

        if len(detections) == 0:
            return np.empty((0, 2), dtype=int), np.empty((0,), dtype=int), np.arange(len(trackers))

        iou_matrix = iou_batch(detections, trackers)

        if min(iou_matrix.shape) > 0:
            a = (iou_matrix > iou_threshold).astype(int)
            if a.sum(1).max() == 1 and a.sum(0).max() == 1:
                matched_indices = np.stack(np.where(a == 1), axis=1)
            else:
                row_ind, col_ind = linear_sum_assignment(-iou_matrix)
                matched_indices = np.asarray(list(zip(row_ind, col_ind)))
        else:
            matched_indices = np.empty((0, 2), dtype=int)

        unmatched_detections = []
        for d, det in enumerate(detections):
            if d not in matched_indices[:, 0]:
                unmatched_detections.append(d)

        unmatched_trackers = []
        for t, trk in enumerate(trackers):
            if t not in matched_indices[:, 1]:
                unmatched_trackers.append(t)

        # Filter out matched pairs with low IOU
        matches = []
        for m in matched_indices:
            if iou_matrix[m[0], m[1]] < iou_threshold:
                unmatched_detections.append(m[0])
                unmatched_trackers.append(m[1])
            else:
                matches.append(m.reshape(1, 2))

        if len(matches) == 0:
            matches = np.empty((0, 2), dtype=int)
        else:
            matches = np.concatenate(matches, axis=0)

        return matches, np.array(unmatched_detections), np.array(unmatched_trackers)
