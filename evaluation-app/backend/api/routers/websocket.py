from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.api.websocket import manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Establish WebSocket connection for real-time evaluation updates.

    Maintains persistent connection to push evaluation progress updates
    to connected clients without polling.

    Args:
        websocket: WebSocket connection to maintain.

    Raises:
        WebSocketDisconnect: When client closes connection.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
