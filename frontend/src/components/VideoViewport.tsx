import React, { useRef } from 'react';
import { Play, Pause, Square, Camera, Maximize2, CameraOff, Video, Sparkles, Loader2 } from 'lucide-react';
import { ConnectionStatus } from '../hooks/useWebSocket';
import { StreamSettings, SystemTelemetry } from '../types';

interface VideoViewportProps {
  currentFrame: string | null;
  connectionStatus: ConnectionStatus;
  isStreaming: boolean;
  isPaused: boolean;
  settings: StreamSettings;
  telemetry: SystemTelemetry;
  webcamPermissionDenied: boolean;
  webcamVideoRef: React.RefObject<HTMLVideoElement>;
  onStart: () => void;
  onPause: () => void;
  onStop: () => void;
  onRequestWebcam: () => void;
}

export const VideoViewport: React.FC<VideoViewportProps> = ({
  currentFrame,
  connectionStatus,
  isStreaming,
  isPaused,
  settings,
  telemetry,
  webcamPermissionDenied,
  webcamVideoRef,
  onStart,
  onPause,
  onStop,
  onRequestWebcam
}) => {
  const containerRef = useRef<HTMLDivElement>(null);

  const toggleFullscreen = () => {
    if (containerRef.current) {
      if (!document.fullscreenElement) {
        containerRef.current.requestFullscreen().catch(err => console.error(err));
      } else {
        document.exitFullscreen().catch(err => console.error(err));
      }
    }
  };

  const downloadSnapshot = () => {
    if (!currentFrame) return;
    const link = document.createElement('a');
    link.href = currentFrame;
    link.download = `vision_ai_snapshot_${Date.now()}.jpg`;
    link.click();
  };

  return (
    <div 
      ref={containerRef}
      className="relative flex flex-col items-center justify-center w-full h-full min-h-[420px] rounded-2xl glass-panel overflow-hidden border border-white/10 shadow-glass group"
    >
      {/* Hidden HTML5 Video element for grabbing webcam frames */}
      <video ref={webcamVideoRef} className="hidden" playsInline muted />

      {/* Main Video Viewport */}
      {currentFrame && isStreaming ? (
        <div className="relative w-full h-full flex items-center justify-center bg-black/80">
          <img 
            src={currentFrame} 
            alt="Annotated Stream" 
            className="w-full h-full max-h-[600px] object-contain transition-opacity duration-150"
          />

          {/* Top-Right Streaming Telemetry Badge */}
          <div className="absolute top-4 right-4 flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-black/60 backdrop-blur-md border border-cyan-500/30 text-xs font-mono">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse-glow" />
            <span className="text-cyan-400 font-semibold">{telemetry.fps} FPS</span>
            <span className="text-slate-500">|</span>
            <span className="text-slate-300">{telemetry.active_tracks_count} Objects</span>
          </div>

          {/* Paused Overlay */}
          {isPaused && (
            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm flex flex-col items-center justify-center space-y-2">
              <Pause className="w-12 h-12 text-cyan-400 animate-pulse" />
              <span className="text-sm font-mono tracking-widest text-cyan-200 uppercase">Stream Paused</span>
            </div>
          )}
        </div>
      ) : (
        /* Empty / Loading / Permission States */
        <div className="flex flex-col items-center justify-center p-8 text-center space-y-4 max-w-md">
          {webcamPermissionDenied ? (
            <div className="p-6 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 space-y-3">
              <CameraOff className="w-12 h-12 mx-auto text-rose-400" />
              <h3 className="text-base font-semibold">Webcam Access Denied</h3>
              <p className="text-xs text-rose-200/80">
                Please grant camera permissions in your browser address bar to use real-time webcam tracking.
              </p>
              <button 
                onClick={onRequestWebcam}
                className="px-4 py-2 text-xs font-semibold rounded-lg bg-rose-500 hover:bg-rose-400 text-black transition-colors"
              >
                Retry Camera Access
              </button>
            </div>
          ) : connectionStatus === 'connecting' ? (
            <div className="space-y-3">
              <Loader2 className="w-10 h-10 mx-auto text-cyan-400 animate-spin" />
              <h3 className="text-sm font-medium text-slate-300">Connecting to Stream Pipeline...</h3>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="relative w-20 h-20 mx-auto flex items-center justify-center rounded-2xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
                <Video className="w-10 h-10" />
                <Sparkles className="w-5 h-5 absolute -top-1 -right-1 text-violet-400 animate-pulse" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-slate-100">Ready to Detect & Track</h3>
                <p className="text-xs text-slate-400 mt-1">
                  Select a stream source (Demo Video, Browser Webcam, or Uploaded Video) and start processing.
                </p>
              </div>
              <button
                onClick={onStart}
                className="inline-flex items-center space-x-2 px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-violet-600 hover:from-cyan-400 hover:to-violet-500 text-slate-950 font-bold text-sm shadow-glow-cyan transition-all transform hover:scale-105"
              >
                <Play className="w-4 h-4 fill-slate-950" />
                <span>Start Stream Pipeline</span>
              </button>
            </div>
          )}
        </div>
      )}

      {/* Floating Bottom Control Toolbar */}
      <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex items-center space-x-2 px-4 py-2 rounded-2xl glass-panel border border-white/10 shadow-2xl backdrop-blur-xl z-20">
        {!isStreaming ? (
          <button
            onClick={onStart}
            className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-black font-bold text-xs transition-colors shadow-glow-cyan"
          >
            <Play className="w-4 h-4 fill-black" />
            <span>Start</span>
          </button>
        ) : (
          <>
            <button
              onClick={onPause}
              className={`p-2.5 rounded-xl transition-colors ${
                isPaused ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40' : 'hover:bg-white/10 text-slate-300'
              }`}
              title={isPaused ? 'Resume' : 'Pause'}
            >
              {isPaused ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
            </button>
            <button
              onClick={onStop}
              className="p-2.5 rounded-xl hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 transition-colors"
              title="Stop"
            >
              <Square className="w-4 h-4 fill-rose-400" />
            </button>
          </>
        )}

        <div className="w-px h-5 bg-white/10 mx-1" />

        <button
          onClick={downloadSnapshot}
          disabled={!currentFrame}
          className="p-2.5 rounded-xl hover:bg-white/10 text-slate-300 disabled:opacity-40 transition-colors"
          title="Take Snapshot"
        >
          <Camera className="w-4 h-4" />
        </button>

        <button
          onClick={toggleFullscreen}
          className="p-2.5 rounded-xl hover:bg-white/10 text-slate-300 transition-colors"
          title="Fullscreen"
        >
          <Maximize2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
