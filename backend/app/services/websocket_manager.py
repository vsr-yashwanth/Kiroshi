import json
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Set, Any, Optional
from fastapi import WebSocket, status
from backend.app.core.logging import logger
from backend.app.domain.models.enums import UserRole


class ConnectionManager:
    """Thread-safe and async connection manager for authenticated authority WebSockets."""

    def __init__(self):
        # Maps user_id -> Set of active WebSocket connections (supports multiple dashboard tabs)
        self._active_connections: Dict[str, Set[WebSocket]] = {}
        self._risk_subscribers: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_id: str, role: str, subscribe_risk: bool = False) -> bool:
        if role not in [UserRole.AUTHORITY.value, UserRole.ADMIN.value]:
            logger.warning(f"Rejecting WebSocket connection: user {user_id} has unauthorized role '{role}'")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return False

        await websocket.accept()
        async with self._lock:
            if user_id not in self._active_connections:
                self._active_connections[user_id] = set()
            self._active_connections[user_id].add(websocket)
            if subscribe_risk:
                self._risk_subscribers.add(websocket)
        logger.info(f"WebSocket client connected: user={user_id}, total_clients={self.total_connections}, risk_subscribers={len(self._risk_subscribers)}")
        return True

    def subscribe_risk(self, websocket: WebSocket):
        self._risk_subscribers.add(websocket)

    def unsubscribe_risk(self, websocket: WebSocket):
        self._risk_subscribers.discard(websocket)

    async def disconnect(self, websocket: WebSocket, user_id: str):
        async with self._lock:
            self._risk_subscribers.discard(websocket)
            if user_id in self._active_connections:
                self._active_connections[user_id].discard(websocket)
                if not self._active_connections[user_id]:
                    del self._active_connections[user_id]
        logger.info(f"WebSocket client disconnected: user={user_id}, remaining={self.total_connections}")

    @property
    def total_connections(self) -> int:
        return sum(len(conns) for conns in self._active_connections.values())

    async def broadcast_json(self, message: Dict[str, Any]):
        """
        Broadcasts a message to all active authority connections.
        Isolates client failures: a broken socket is cleanly removed without affecting others.
        """
        data_str = json.dumps(message, default=str)
        dead_connections: list[tuple[str, WebSocket]] = []

        async with self._lock:
            all_connections = [
                (uid, ws) for uid, conns in self._active_connections.items() for ws in conns
            ]

        for uid, ws in all_connections:
            try:
                await ws.send_text(data_str)
            except Exception as e:
                logger.warning(f"Error sending message to client {uid}: {e}. Queuing for cleanup.")
                dead_connections.append((uid, ws))

        # Clean up any dead connections
        if dead_connections:
            async with self._lock:
                for uid, ws in dead_connections:
                    if uid in self._active_connections:
                        self._active_connections[uid].discard(ws)
                        if not self._active_connections[uid]:
                            del self._active_connections[uid]

    async def broadcast_location_update(self, payload: Dict[str, Any]):
        await self.broadcast_json({
            "type": "LOCATION_UPDATE",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": payload,
        })

    async def broadcast_zone_event(self, event_type: str, payload: Dict[str, Any]):
        await self.broadcast_json({
            "type": f"ZONE_{event_type}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": payload,
        })

    async def broadcast_risk_update(self, payload: Dict[str, Any]):
        message = {
            "type": "RISK_UPDATE",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": payload,
        }
        data_str = json.dumps(message, default=str)
        async with self._lock:
            subscribers = list(self._risk_subscribers)

        for ws in subscribers:
            try:
                await ws.send_text(data_str)
            except Exception as e:
                logger.warning(f"Error sending risk update to subscriber: {e}")
                self._risk_subscribers.discard(ws)
    async def broadcast_incident_event(self, event_type: str, payload: Dict[str, Any]):
        await self.broadcast_json({
            "type": f"INCIDENT_{event_type}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": payload,
        })


# Global singleton manager instance
ws_manager = ConnectionManager()

