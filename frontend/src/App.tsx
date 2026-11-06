import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Header } from './components/Header';
import { VideoViewport } from './components/VideoViewport';
import { ControlsPanel } from './components/ControlsPanel';
import { AnalyticsDashboard } from './components/AnalyticsDashboard';
import { TrackedTable } from './components/TrackedTable';
import { BackgroundParticles } from './components/BackgroundParticles';
import { useWebSocket } from './hooks/useWebSocket';
import { useWebcam } from './hooks/useWebcam';
import { StreamSettings } from './types';

export const App: React.FC = () => {
  const [settings, setSettings] = useState<StreamSettings>({
    source: 'demo',
    model: 'yolov8n',
    tracker: 'sort',
    confidence: 0.35,
    frameSkip: 1,
  });

  const [isStreaming, setIsStreaming] = useState(false);
  const [isPaused, setIsPaused] = useState(false);

  const {
    status: connectionStatus,
    currentFrame,
    trackedObjects,
    telemetry,
    latencyMs,
    sendConfig,
    sendStart,
    sendPause,
    sendStop,
    sendWebcamFrame
  } = useWebSocket();

  const {
    permissionDenied: webcamPermissionDenied,
    videoRef: webcamVideoRef,
    startWebcam,
    stopWebcam,
    captureFrameBlob
  } = useWebcam();

  const webcamIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Send config updates whenever settings change
  const handleUpdateSettings = (newSettings: Partial<StreamSettings>) => {
    const updated = { ...settings, ...newSettings };
    setSettings(updated);
    sendConfig(updated);
  };

  // Upload custom video file to backend REST API
  const handleUploadFile = async (file: File): Promise<boolean> => {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) return false;

      const data = await response.json();
      if (data.status === 'success') {
        const updated = { ...settings, source: 'file' as const, uploadedFilename: data.filename };
        setSettings(updated);
        sendConfig(updated);
        return true;
      }
      return false;
    } catch (err) {
      console.error('File upload error:', err);
      return false;
    }
  };

  // Start processing pipeline
  const handleStartStream = async () => {
    if (settings.source === 'webcam') {
      const granted = await startWebcam();
      if (!granted) return;

      // Start capturing webcam frame blobs and sending over WebSocket
      if (webcamIntervalRef.current) clearInterval(webcamIntervalRef.current);
      webcamIntervalRef.current = setInterval(async () => {
        const blob = await captureFrameBlob();
        if (blob) {
          sendWebcamFrame(blob);
        }
      }, 40); // ~25 FPS
    } else {
      stopWebcam();
      if (webcamIntervalRef.current) clearInterval(webcamIntervalRef.current);
    }

    sendStart(settings);
    setIsStreaming(true);
    setIsPaused(false);
  };

  const handlePauseStream = () => {
    sendPause();
    setIsPaused(!isPaused);
  };

  const handleStopStream = () => {
    sendStop();
    stopWebcam();
    if (webcamIntervalRef.current) clearInterval(webcamIntervalRef.current);
    setIsStreaming(false);
    setIsPaused(false);
  };

  // Clean up timers on unmount
  useEffect(() => {
    return () => {
      if (webcamIntervalRef.current) clearInterval(webcamIntervalRef.current);
    };
  }, []);

  return (
    <div className="relative min-h-screen flex flex-col z-10">
      <BackgroundParticles />
      
      {/* Top Header */}
      <Header
        connectionStatus={connectionStatus}
        latencyMs={latencyMs}
        settings={settings}
      />

      {/* Main Content Dashboard */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 space-y-6">
        {/* Top Section: Central Viewport + Right Controls Panel */}
        <div className="flex flex-col lg:flex-row gap-6 items-stretch">
          {/* Main Central Viewport */}
          <div className="flex-1 min-w-0">
            <VideoViewport
              currentFrame={currentFrame}
              connectionStatus={connectionStatus}
              isStreaming={isStreaming}
              isPaused={isPaused}
              settings={settings}
              telemetry={telemetry}
              webcamPermissionDenied={webcamPermissionDenied}
              webcamVideoRef={webcamVideoRef}
              onStart={handleStartStream}
              onPause={handlePauseStream}
              onStop={handleStopStream}
              onRequestWebcam={startWebcam}
            />
          </div>

          {/* Right Controls Panel */}
          <ControlsPanel
            settings={settings}
            onUpdateSettings={handleUpdateSettings}
            onUploadFile={handleUploadFile}
          />
        </div>

        {/* Analytics Telemetry Widgets */}
        <AnalyticsDashboard telemetry={telemetry} />

        {/* Tracked Objects Table */}
        <TrackedTable trackedObjects={trackedObjects} />
      </main>
    </div>
  );
};

export default App;
