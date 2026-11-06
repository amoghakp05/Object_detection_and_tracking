import React, { useState } from 'react';
import { Sliders, Video, Camera, Upload, Cpu, Activity, Zap, Check, AlertCircle } from 'lucide-react';
import { StreamSettings, StreamSource, ModelType, TrackerType, ModelOption, TrackerOption } from '../types';

interface ControlsPanelProps {
  settings: StreamSettings;
  onUpdateSettings: (newSettings: Partial<StreamSettings>) => void;
  onUploadFile: (file: File) => Promise<boolean>;
}

const MODEL_OPTIONS: ModelOption[] = [
  { id: 'yolov8n', name: 'YOLOv8 Nano', speed: 'Ultra Fast (30+ FPS)', accuracy: 'Good' },
  { id: 'yolov8s', name: 'YOLOv8 Small', speed: 'Fast (25+ FPS)', accuracy: 'High' },
  { id: 'yolov8m', name: 'YOLOv8 Medium', speed: 'Medium (15+ FPS)', accuracy: 'Very High' },
  { id: 'faster_rcnn', name: 'Faster R-CNN', speed: 'Precision (CPU)', accuracy: 'Max Precision' },
];

const TRACKER_OPTIONS: TrackerOption[] = [
  { id: 'sort', name: 'SORT Tracker', description: 'Kalman Filter + Hungarian IOU matching' },
  { id: 'deep_sort', name: 'Deep SORT Tracker', description: 'Deep appearance embeddings for occluded scenes' },
];

export const ControlsPanel: React.FC<ControlsPanelProps> = ({
  settings,
  onUpdateSettings,
  onUploadFile,
}) => {
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadError(null);

    const success = await onUploadFile(file);
    setUploading(false);

    if (!success) {
      setUploadError('Failed to upload video file. Check file format (MP4, AVI, MOV).');
    }
  };

  return (
    <aside className="w-full lg:w-80 flex-shrink-0 flex flex-col space-y-4">
      <div className="glass-panel p-5 rounded-2xl border border-white/10 shadow-glass space-y-5">
        {/* Panel Header */}
        <div className="flex items-center justify-between pb-3 border-b border-white/10">
          <div className="flex items-center space-x-2">
            <Sliders className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-bold tracking-wider text-slate-100 uppercase">Stream Controls</h2>
          </div>
          <span className="text-[10px] font-mono text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded-full border border-cyan-500/20">
            CONFIG
          </span>
        </div>

        {/* 1. Video Source Selector */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center space-x-1.5">
            <Video className="w-3.5 h-3.5 text-cyan-400" />
            <span>Video Source</span>
          </label>
          <div className="grid grid-cols-3 gap-1.5 p-1 rounded-xl bg-slate-900/80 border border-white/10">
            {(['demo', 'webcam', 'file'] as StreamSource[]).map((src) => (
              <button
                key={src}
                onClick={() => onUpdateSettings({ source: src })}
                className={`py-2 px-1 text-xs font-medium rounded-lg capitalize transition-all ${
                  settings.source === src
                    ? 'bg-cyan-500 text-slate-950 font-bold shadow-glow-cyan'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
                }`}
              >
                {src}
              </button>
            ))}
          </div>

          {/* Upload File Zone */}
          {settings.source === 'file' && (
            <div className="mt-2 space-y-2">
              <label className="relative flex flex-col items-center justify-center p-4 border-2 border-dashed border-cyan-500/30 rounded-xl bg-cyan-500/5 hover:bg-cyan-500/10 cursor-pointer transition-colors text-center">
                <Upload className="w-6 h-6 text-cyan-400 mb-1" />
                <span className="text-xs font-medium text-slate-200">
                  {uploading ? 'Uploading Video...' : settings.uploadedFilename ? `File: ${settings.uploadedFilename}` : 'Click to Upload Video'}
                </span>
                <span className="text-[10px] text-slate-400">MP4, AVI, MOV, WEBM</span>
                <input
                  type="file"
                  accept="video/*"
                  onChange={handleFileChange}
                  className="hidden"
                />
              </label>
              {uploadError && (
                <div className="flex items-center space-x-1 text-[11px] text-rose-400">
                  <AlertCircle className="w-3.5 h-3.5" />
                  <span>{uploadError}</span>
                </div>
              )}
            </div>
          )}
        </div>

        {/* 2. Model Selector */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center space-x-1.5">
            <Cpu className="w-3.5 h-3.5 text-cyan-400" />
            <span>Detection Model</span>
          </label>
          <div className="space-y-1.5">
            {MODEL_OPTIONS.map((opt) => (
              <button
                key={opt.id}
                onClick={() => onUpdateSettings({ model: opt.id })}
                className={`w-full p-2.5 rounded-xl border text-left flex items-center justify-between transition-all ${
                  settings.model === opt.id
                    ? 'bg-cyan-500/10 border-cyan-500 text-slate-100 shadow-glow-cyan'
                    : 'bg-slate-900/40 border-white/5 text-slate-400 hover:border-white/20'
                }`}
              >
                <div>
                  <div className="text-xs font-bold text-slate-200 flex items-center space-x-1.5">
                    <span>{opt.name}</span>
                    {settings.model === opt.id && <Check className="w-3 h-3 text-cyan-400" />}
                  </div>
                  <div className="text-[10px] text-slate-400">{opt.speed}</div>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-cyan-300">
                  {opt.accuracy}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* 3. Tracker Selector */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center space-x-1.5">
            <Activity className="w-3.5 h-3.5 text-violet-400" />
            <span>Multi-Object Tracker</span>
          </label>
          <div className="grid grid-cols-2 gap-2">
            {TRACKER_OPTIONS.map((tr) => (
              <button
                key={tr.id}
                onClick={() => onUpdateSettings({ tracker: tr.id })}
                className={`p-2.5 rounded-xl border text-left transition-all ${
                  settings.tracker === tr.id
                    ? 'bg-violet-500/10 border-violet-500 text-slate-100 shadow-glow-violet'
                    : 'bg-slate-900/40 border-white/5 text-slate-400 hover:border-white/20'
                }`}
              >
                <div className="text-xs font-bold text-slate-200">{tr.name}</div>
                <div className="text-[10px] text-slate-400 mt-1 line-clamp-2">{tr.description}</div>
              </button>
            ))}
          </div>
        </div>

        {/* 4. Confidence Threshold Slider */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center space-x-1.5">
              <Zap className="w-3.5 h-3.5 text-amber-400" />
              <span>Confidence Threshold</span>
            </label>
            <span className="text-xs font-mono text-cyan-400 font-bold">
              {Math.round(settings.confidence * 100)}%
            </span>
          </div>
          <input
            type="range"
            min="0.1"
            max="0.9"
            step="0.05"
            value={settings.confidence}
            onChange={(e) => onUpdateSettings({ confidence: parseFloat(e.target.value) })}
            className="w-full accent-cyan-400 bg-slate-800 rounded-lg h-1.5 cursor-pointer"
          />
        </div>

        {/* 5. Adaptive Frame Skipping (CPU Throttling) */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Frame Throttling
            </label>
            <span className="text-xs font-mono text-violet-400">
              {settings.frameSkip === 1 ? 'Every Frame (1x)' : `Every ${settings.frameSkip} Frames`}
            </span>
          </div>
          <input
            type="range"
            min="1"
            max="4"
            step="1"
            value={settings.frameSkip}
            onChange={(e) => onUpdateSettings({ frameSkip: parseInt(e.target.value) })}
            className="w-full accent-violet-400 bg-slate-800 rounded-lg h-1.5 cursor-pointer"
          />
        </div>
      </div>
    </aside>
  );
};
