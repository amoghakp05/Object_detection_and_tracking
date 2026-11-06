export interface BoundingBox {
  0: number; // x1
  1: number; // y1
  2: number; // x2
  3: number; // y2
}

export interface TrackedObject {
  id: number;
  bbox: [number, number, number, number];
  class_id: number;
  class_name: string;
  confidence: number;
  duration_frames: number;
}

export interface SystemTelemetry {
  fps: number;
  inference_time_ms: number;
  active_tracks_count: number;
  total_objects_count: number;
  class_counts: Record<string, number>;
  frame_index: number;
  model: string;
  tracker: string;
}

export type StreamSource = 'demo' | 'webcam' | 'file';
export type ModelType = 'yolov8n' | 'yolov8s' | 'yolov8m' | 'faster_rcnn';
export type TrackerType = 'sort' | 'deep_sort';

export interface StreamSettings {
  source: StreamSource;
  model: ModelType;
  tracker: TrackerType;
  confidence: number;
  frameSkip: number;
  uploadedFilename?: string;
}

export interface ModelOption {
  id: ModelType;
  name: string;
  speed: string;
  accuracy: string;
}

export interface TrackerOption {
  id: TrackerType;
  name: string;
  description: string;
}
