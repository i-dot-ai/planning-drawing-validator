import { useEffect, useRef, useState, useCallback } from "react";
import { WebSocketMessage } from "../types";
import {
  WEBSOCKET_CONFIG,
  CONNECTION_STATUS,
  type ConnectionStatus,
} from "../lib/constants";

/**
 * Custom hook for WebSocket connection management
 *
 * Handles connection lifecycle, automatic reconnection, and message parsing.
 * Connects to backend WebSocket endpoint with proper error handling.
 *
 * @param onMessage - Callback for handling received messages
 * @returns Connection status and WebSocket instance
 */
export function useWebSocket(onMessage: (message: WebSocketMessage) => void) {
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>(
    CONNECTION_STATUS.DISCONNECTED,
  );
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | undefined>(undefined);

  const connect = useCallback(() => {
    // Don't connect if already connected
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setConnectionStatus(CONNECTION_STATUS.CONNECTING);

    // Determine WebSocket protocol and host
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    let host = window.location.host;

    // In development, connect directly to backend port
    if (host.endsWith(`:${WEBSOCKET_CONFIG.DEV_PORT}`)) {
      host = host.replace(
        `:${WEBSOCKET_CONFIG.DEV_PORT}`,
        `:${WEBSOCKET_CONFIG.BACKEND_PORT}`,
      );
    }

    const websocket = new WebSocket(`${protocol}//${host}/ws`);

    websocket.onopen = () => {
      setConnectionStatus(CONNECTION_STATUS.CONNECTED);
      wsRef.current = websocket;
    };

    websocket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as WebSocketMessage;
        onMessage(message);
      } catch (error) {
        console.error("Failed to parse WebSocket message:", error);
      }
    };

    websocket.onclose = () => {
      setConnectionStatus(CONNECTION_STATUS.DISCONNECTED);
      wsRef.current = null;

      // Attempt to reconnect after delay
      reconnectTimeoutRef.current = setTimeout(
        connect,
        WEBSOCKET_CONFIG.RECONNECT_DELAY,
      );
    };

    websocket.onerror = (error) => {
      console.error("WebSocket error:", error);
      setConnectionStatus(CONNECTION_STATUS.DISCONNECTED);
    };
  }, [onMessage]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  return { connectionStatus, ws: wsRef.current };
}
