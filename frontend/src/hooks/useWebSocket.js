/**
 * useWebSocket — Custom hook for managing WebSocket connection to backend.
 *
 * Provides auto-reconnect with exponential backoff, message sending,
 * and structured event handling.
 */

import { useRef, useState, useCallback, useEffect } from 'react';

const DEFAULT_URL = `ws://${window.location.hostname}:8000/ws/translate`;
const MAX_RECONNECT_DELAY = 10000;
const INITIAL_RECONNECT_DELAY = 1000;

export function useWebSocket(url = DEFAULT_URL) {
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);
  const reconnectDelay = useRef(INITIAL_RECONNECT_DELAY);

  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const [error, setError] = useState(null);

  /**
   * Connect to the WebSocket server.
   */
  const connect = useCallback(() => {
    // Don't connect if already connected
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        console.log('[WS] Connected to', url);
        setIsConnected(true);
        setError(null);
        reconnectDelay.current = INITIAL_RECONNECT_DELAY;
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setLastMessage(data);
        } catch {
          console.warn('[WS] Non-JSON message received:', event.data);
        }
      };

      ws.onclose = (event) => {
        console.log('[WS] Disconnected:', event.code, event.reason);
        setIsConnected(false);
        wsRef.current = null;

        // Auto-reconnect with exponential backoff
        if (!event.wasClean) {
          reconnectTimer.current = setTimeout(() => {
            console.log(`[WS] Reconnecting in ${reconnectDelay.current}ms...`);
            connect();
            reconnectDelay.current = Math.min(
              reconnectDelay.current * 2,
              MAX_RECONNECT_DELAY
            );
          }, reconnectDelay.current);
        }
      };

      ws.onerror = (event) => {
        console.error('[WS] Error:', event);
        setError('WebSocket connection error');
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('[WS] Failed to create WebSocket:', err);
      setError(err.message);
    }
  }, [url]);

  /**
   * Disconnect from the WebSocket server.
   */
  const disconnect = useCallback(() => {
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'Client disconnect');
      wsRef.current = null;
    }

    setIsConnected(false);
  }, []);

  /**
   * Send a video frame to the backend.
   * @param {string} base64Data - Base64-encoded JPEG frame.
   */
  const sendFrame = useCallback((base64Data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'frame',
          data: base64Data,
        })
      );
    }
  }, []);

  /**
   * Send a control message to the backend.
   * @param {string} action - Control action (start|stop|next_word|finish|clear).
   */
  const sendControl = useCallback((action) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'control',
          action: action,
        })
      );
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    isConnected,
    lastMessage,
    error,
    connect,
    disconnect,
    sendFrame,
    sendControl,
  };
}
