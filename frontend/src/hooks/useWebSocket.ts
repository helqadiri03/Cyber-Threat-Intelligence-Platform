import { useCallback, useEffect, useRef, useState } from 'react';

const WS_BASE = import.meta.env.VITE_WS_BASE_URL ?? 'ws://localhost:8000';
const MAX_ALERTS = 100;
const BASE_DELAY_MS = 1_000;
const MAX_DELAY_MS = 30_000;

export interface LiveAlert {
  id: string;
  source_ip: string;
  predicted_attack: string;
  confidence: number;
  risk_score: number;
  model_version?: string;
  timestamp: string;
}

export type WsStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

export function useWebSocket() {
  const [alerts, setAlerts] = useState<LiveAlert[]>([]);
  const [status, setStatus] = useState<WsStatus>('connecting');

  const wsRef = useRef<WebSocket | null>(null);
  const retryCountRef = useRef(0);
  const retryTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);

  const clearRetryTimer = () => {
    if (retryTimerRef.current !== null) {
      clearTimeout(retryTimerRef.current);
      retryTimerRef.current = null;
    }
  };

  const connect = useCallback(() => {
    if (!mountedRef.current) return;
    setStatus('connecting');

    const ws = new WebSocket(`${WS_BASE}/ws/live`);
    wsRef.current = ws;

    ws.onopen = () => {
      if (!mountedRef.current) { ws.close(); return; }
      setStatus('connected');
      retryCountRef.current = 0;
    };

    ws.onmessage = (event) => {
      if (!mountedRef.current) return;
      try {
        const raw = JSON.parse(event.data as string) as Record<string, any>;
        
        // Ignore control messages
        if (raw.type === 'connected' || raw.type === 'pong' || raw.type === 'ping') {
          return;
        }

        // The backend wraps alerts in { type: "alert", data: {...} }
        const payload = raw.type === 'alert' ? raw.data : raw;

        const alert: LiveAlert = {
          id: payload.id ?? crypto.randomUUID(),
          source_ip: payload.source_ip ?? '0.0.0.0',
          predicted_attack: payload.predicted_attack ?? 'Unknown',
          confidence: payload.confidence ?? 0,
          risk_score: payload.risk_score ?? 0,
          model_version: payload.model_version,
          timestamp: payload.timestamp ?? new Date().toISOString(),
        };
        setAlerts((prev) => [alert, ...prev].slice(0, MAX_ALERTS));
      } catch {
        // ignore malformed messages
      }
    };

    ws.onerror = () => {
      if (!mountedRef.current) return;
      setStatus('error');
    };

    ws.onclose = () => {
      if (!mountedRef.current) return;
      setStatus('disconnected');
      // Exponential backoff with jitter
      const delay = Math.min(BASE_DELAY_MS * 2 ** retryCountRef.current, MAX_DELAY_MS);
      retryCountRef.current += 1;
      retryTimerRef.current = setTimeout(connect, delay);
    };
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    connect();
    return () => {
      mountedRef.current = false;
      clearRetryTimer();
      wsRef.current?.close();
    };
  }, [connect]);

  const clearAlerts = useCallback(() => setAlerts([]), []);

  return { alerts, status, clearAlerts };
}
