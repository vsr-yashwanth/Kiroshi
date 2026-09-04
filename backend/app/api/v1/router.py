from fastapi import APIRouter
from backend.app.api.v1.endpoints import health, auth, tourists, trips, location, zones, websocket, risk

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(tourists.router, prefix="/tourists", tags=["Tourists"])
api_router.include_router(trips.router, prefix="/trips", tags=["Trips"])
api_router.include_router(location.router, prefix="/location", tags=["Location"])
api_router.include_router(zones.router, prefix="/zones", tags=["GeoZones"])
api_router.include_router(websocket.router, prefix="/ws", tags=["WebSockets"])
api_router.include_router(risk.router, prefix="/risk", tags=["Risk Engine"])


