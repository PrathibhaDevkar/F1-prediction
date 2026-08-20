import os

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from services.live_timing import LiveTelemetryManager

router = APIRouter(tags=["live"])

manager = LiveTelemetryManager(api_key=os.getenv("OPENF1_API_KEY"))


@router.websocket("/ws/live-timing")
async def live_timing_ws(websocket: WebSocket):
    await websocket.accept()
    manager.subscribe(websocket)
    await websocket.send_json(manager.snapshot())
    try:
        while True:
            # Keep-alive / disconnect detection; the client doesn't need to
            # send anything meaningful, this just blocks until it goes away.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.unsubscribe(websocket)
