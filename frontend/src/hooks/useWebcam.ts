import { useState, useRef, useCallback, useEffect } from 'react';

interface UseWebcamReturn {
  isStreaming: boolean;
  permissionDenied: boolean;
  videoRef: React.RefObject<HTMLVideoElement>;
  startWebcam: () => Promise<boolean>;
  stopWebcam: () => void;
  captureFrameBlob: () => Promise<Blob | null>;
}

export function useWebcam(): UseWebcamReturn {
  const [isStreaming, setIsStreaming] = useState(false);
  const [permissionDenied, setPermissionDenied] = useState(false);
  
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    // Create hidden canvas for frame grabbing
    canvasRef.current = document.createElement('canvas');
    canvasRef.current.width = 640;
    canvasRef.current.height = 480;
  }, []);

  const startWebcam = useCallback(async (): Promise<boolean> => {
    try {
      setPermissionDenied(false);
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, frameRate: { ideal: 30 } },
        audio: false
      });
      
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setIsStreaming(true);
      return true;
    } catch (err) {
      console.error('Webcam permission denied or error:', err);
      setPermissionDenied(true);
      setIsStreaming(false);
      return false;
    }
  }, []);

  const stopWebcam = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setIsStreaming(false);
  }, []);

  const captureFrameBlob = useCallback((): Promise<Blob | null> => {
    return new Promise((resolve) => {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      if (!video || !canvas || video.readyState < 2) {
        resolve(null);
        return;
      }

      const ctx = canvas.getContext('2d');
      if (!ctx) {
        resolve(null);
        return;
      }

      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      canvas.toBlob((blob) => {
        resolve(blob);
      }, 'image/jpeg', 0.8);
    });
  }, []);

  return {
    isStreaming,
    permissionDenied,
    videoRef,
    startWebcam,
    stopWebcam,
    captureFrameBlob
  };
}
