import json
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import SessionLocal
from backend.app.core.security import decode_access_token
from backend.app.core.logging import logger
from backend.app.domain.models.enums import UserRole
from backend.app.services.websocket_manager import ws_manager
from backend.app.services.location_service import LocationService

router = APIRouter()


@router.websocket("/authority")
async def authority_websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    """
    Authenticated WebSocket endpoint for Authority Dashboard live geospatial stream.
    Streams location updates, GeoZone ENTER/EXIT events, and system heartbeats.
    """
    if not token:
        logger.warning("WebSocket connection attempt missing token query parameter.")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    payload = decode_access_token(token)
    if not payload:
        logger.warning("WebSocket connection attempt with invalid or expired JWT token.")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id = payload.get("sub")
    role = payload.get("role")

    if not user_id or role not in [UserRole.AUTHORITY.value, UserRole.ADMIN.value]:
        logger.warning(f"WebSocket connection rejected: user {user_id} has unauthorized role '{role}'")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Accept connection and register with manager
    accepted = await ws_manager.connect(websocket, user_id=user_id, role=role)
    if not accepted:
        return

    db: Session = SessionLocal()
    try:
        # Send initial snapshot of currently active tourists and their latest positions
        service = LocationService(db)
        snapshot = service.get_active_tourists_snapshot()
        snapshot_data = [pos.model_dump(mode="json") for pos in snapshot]

        await websocket.send_text(
            json.dumps({
                "type": "INITIAL_SNAPSHOT",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": snapshot_data,
            })
        )

        # Message receiver loop for heartbeats and keepalives
        while True:
            raw_text = await websocket.receive_text()
            try:
                data = json.loads(raw_text)
                msg_type = data.get("type", "").upper()
                if msg_type == "PING":
                    await websocket.send_text(
                        json.dumps({
                            "type": "PONG",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        })
                    )
            except json.JSONDecodeError:
                logger.debug(f"Received non-JSON message from client {user_id}: {raw_text}")
                continue

    except WebSocketDisconnect:
        logger.info(f"Authority WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"Unexpected WebSocket error for user {user_id}: {e}")
    finally:
        db.close()
        await ws_manager.disconnect(websocket, user_id=user_id)
