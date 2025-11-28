import json
import logging
from typing import Any

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect, WebSocketState

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection.

        Args:
            websocket: WebSocket connection to register.
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """Unregister a WebSocket connection.

        Args:
            websocket: WebSocket connection to remove.
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast message to all connected clients.

        Sends the message to all active WebSocket connections. Automatically
        handles disconnections and removes stale connections.

        Args:
            message: Dictionary to send as JSON to all clients.
        """
        if not self.active_connections:
            logger.debug("No active WebSocket connections to broadcast to")
            return

        disconnected = []
        message_json = json.dumps(message)

        for connection in self.active_connections:
            try:
                # Check if connection is still open
                if connection.client_state != WebSocketState.CONNECTED:
                    logger.debug("WebSocket not in connected state, marking for cleanup")
                    disconnected.append(connection)
                    continue

                await connection.send_text(message_json)
            except WebSocketDisconnect as e:
                logger.info(f"WebSocket disconnected during broadcast: {e}")
                disconnected.append(connection)
            except RuntimeError as e:
                # Handle "WebSocket is not connected" errors
                logger.warning(f"WebSocket runtime error during broadcast: {e}")
                disconnected.append(connection)
            except Exception as e:
                logger.error(f"Unexpected error broadcasting to WebSocket: {e}", exc_info=True)
                disconnected.append(connection)

        # Clean up disconnected clients
        if disconnected:
            logger.info(f"Cleaning up {len(disconnected)} disconnected WebSocket(s)")
            for conn in disconnected:
                self.disconnect(conn)


# Global connection manager instance
manager = ConnectionManager()
