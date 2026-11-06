import { useState, useEffect, useRef, useCallback } from 'react';
import { TrackedObject, SystemTelemetry, StreamSettings } from '../types';

export type ConnectionStatus = 'connected' | 'connecting' | 'disconnected' | 'error';

interface UseWebSocketReturn {
  status: ConnectionStatus;
  currentFrame: string | null;
  trackedObjects: TrackedObject[];
  telemetry: SystemTelemetry;
  latencyMs: number;
  sendConfig: (settings: StreamSettings) => void;
  sendStart: (settings: StreamSettings) => void;
  sendPause: () => void;
  sendStop: () => void;
  sendWebcamFrame: (blob: Blob) => void;
}

const initialTelemetry: SystemTelemetry = {
  fps: 0,
  inference_time_ms: 0,
  active_tracks_count: 0,
  total_objects_count: 0,
  class_counts: {},
  frame_index: 0,
  model: 'yolov8n',
  tracker: 'sort',
};

export function useWebSocket(): UseWebSocketReturn {
  const [status, setStatus] = useState<ConnectionStatus>('disconnected');
  const [currentFrame, setCurrentFrame] = useState<string | null>(null);
  const [trackedObjects, setTrackedObjects] = useState<TrackedObject[]>([]);
  const [telemetry, setTelemetry] = useState<SystemTelemetry>(initialTelemetry);
  const [latencyMs, setLatencyMs] = useState<number>(0);

  const wsRef = useRef<WebSocket | null>(null);
  const lastPingTimeRef = useRef<number>(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isMountedRef = useRef<boolean>(true);

  const connect = useCallback(() => {
    try {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }

      setStatus('connecting');
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const wsUrl = `${protocol}//${host}/ws/stream`;

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        if (wsRef.current === ws && isMountedRef.current) {
          setStatus('connected');
          console.log('WebSocket connected');
        }
      };

      ws.onmessage = (event) => {
        if (wsRef.current !== ws || !isMountedRef.current) return;
        const receiveTime = Date.now();
        if (lastPingTimeRef.current > 0) {
          setLatencyMs(receiveTime - lastPingTimeRef.current);
          lastPingTimeRef.current = 0;
        }

        try {
          const data = JSON.parse(event.data);
          if (data.type === 'frame') {
            setCurrentFrame(data.image);
            setTrackedObjects(data.objects || []);
            if (data.telemetry) {
              setTelemetry(data.telemetry);
            }
          }
        } catch (e) {
          console.error('Error parsing WS message:', e);
        }
      };

      ws.onerror = (err) => {
        if (wsRef.current === ws && isMountedRef.current) {
          console.error('WebSocket error:', err);
          setStatus('error');
        }
      };

      ws.onclose = () => {
        if (wsRef.current === ws) {
          wsRef.current = null;
          if (isMountedRef.current) {
            setStatus('disconnected');
            console.log('WebSocket disconnected, retrying in 3s...');
            reconnectTimeoutRef.current = setTimeout(() => {
              if (isMountedRef.current) {
                connect();
              }
            }, 3000);
          }
        }
      };
    } catch (err) {
      console.error('WebSocket connection setup error:', err);
      if (isMountedRef.current) {
        setStatus('error');
        reconnectTimeoutRef.current = setTimeout(() => {
          if (isMountedRef.current) {
            connect();
          }
        }, 3000);
      }
    }
  }, []);

  useEffect(() => {
    isMountedRef.current = true;
    connect();
    return () => {
      isMountedRef.current = false;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
      if (wsRef.current) {
        const socketToClose = wsRef.current;
        wsRef.current = null;
        socketToClose.close();
      }
    };
  }, [connect]);

  const sendConfig = useCallback((settings: StreamSettings) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      lastPingTimeRef.current = Date.now();
      wsRef.current.send(JSON.stringify({
        type: 'config',
        model: settings.model,
        tracker: settings.tracker,
        confidence: settings.confidence,
        frame_skip: settings.frameSkip
      }));
    }
  }, []);

  const sendStart = useCallback((settings: StreamSettings) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'start',
        source: settings.source,
        filename: settings.uploadedFilename || ''
      }));
    }
  }, []);

  const sendPause = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'pause' }));
    }
  }, []);

  const sendStop = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'stop' }));
    }
  }, []);

  const sendWebcamFrame = useCallback((blob: Blob) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(blob);
    }
  }, []);

  return {
    status,
    currentFrame,
    trackedObjects,
    telemetry,
    latencyMs,
    sendConfig,
    sendStart,
    sendPause,
    sendStop,
    sendWebcamFrame
  };
}
