import { useEffect, useRef, useState, useCallback } from 'react';
import { WS_BASE_URL, getApiToken } from '../api/client';

export interface WsEvent {
  type: string;
  task_id?: string;
  payload?: any;
  task?: any;
}

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected';

export const useWebSocket = (onEvent?: (event: WsEvent) => void) => {
  const [status, setStatus] = useState<ConnectionStatus>('disconnected');
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const callbackRef = useRef(onEvent);

  // Keep callback reference updated without re-triggering connection resets
  useEffect(() => {
    callbackRef.current = onEvent;
  }, [onEvent]);

  const connect = useCallback(() => {
    if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }

    const token = getApiToken();
    const wsUrl = `${WS_BASE_URL}/ws?token=${encodeURIComponent(token)}`;

    setStatus('connecting');
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus('connected');
      console.log('[WebSocket] Connection established successfully.');
    };

    ws.onmessage = (event) => {
      try {
        const parsed: WsEvent = JSON.parse(event.data);
        if (callbackRef.current) {
          callbackRef.current(parsed);
        }
      } catch (err) {
        console.error('[WebSocket] Failed to parse incoming event message:', err);
      }
    };

    ws.onclose = (event) => {
      setStatus('disconnected');
      wsRef.current = null;
      console.log(`[WebSocket] Connection closed (code: ${event.code}). Reconnecting in 3s...`);
      
      // Auto-reconnect after 3 seconds
      reconnectTimeoutRef.current = window.setTimeout(() => {
        connect();
      }, 3000);
    };

    ws.onerror = (err) => {
      console.error('[WebSocket] Socket encountered error:', err);
      ws.close();
    };
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (wsRef.current) {
      // Clear event listeners first to prevent auto-reconnection loop on manual disconnect
      wsRef.current.onclose = null;
      wsRef.current.onerror = null;
      wsRef.current.close();
      wsRef.current = null;
    }
    setStatus('disconnected');
  }, []);

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  // Expose send helper for future client-to-server WS messages
  const send = useCallback((message: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
      return true;
    }
    return false;
  }, []);

  return {
    status,
    connect,
    disconnect,
    send,
  };
};
