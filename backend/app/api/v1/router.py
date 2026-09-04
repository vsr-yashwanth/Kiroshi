from fastapi import APIRouter
from backend.app.api.v1.endpoints import health, auth, tourists, trips

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(tourists.router, prefix="/tourists", tags=["Tourists"])
api_router.include_router(trips.router, prefix="/trips", tags=["Trips"])
