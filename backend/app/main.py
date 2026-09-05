import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core import database
from backend.app.core.errors import AppException
from backend.app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing KIROSHI Backend Platform v%s...", settings.VERSION)
    # Create tables if not existing (SQLite / Local dev fallback)
    try:
        database.Base.metadata.create_all(bind=database.engine)
        logger.info("Database schemas verified.")
    except Exception as exc:
        logger.warning("Database schema initialization skipped or already handled: %s", exc)
    yield
    logger.info("Shutting down KIROSHI Backend Platform...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="KIROSHI: Smart Tourist Safety Monitoring & Incident Response System — Core Platform API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_and_timing_middleware(request: Request, call_next):
    """
    Standardized observability middleware.
    Injects unique X-Request-ID and tracks millisecond latency.
    """
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id

    start_time = time.perf_counter()
    try:
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-MS"] = str(duration_ms)

        # Skip spamming logs for frequent health checks
        if not request.url.path.endswith("/health") and not request.url.path.endswith("/ready"):
            logger.info(
                "%s %s -> %s (%sms)",
                request.method,
                request.url.path,
                response.status_code,
                duration_ms,
                extra={"request_id": request_id, "status_code": response.status_code, "duration_ms": duration_ms},
            )
        return response
    except Exception as exc:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.error(
            "Unhandled server error on %s %s: %s",
            request.method,
            request.url.path,
            str(exc),
            extra={"request_id": request_id, "duration_ms": duration_ms},
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal server error occurred. Please contact system administrator.", "request_id": request_id},
            headers={"X-Request-ID": request_id},
        )


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    headers = exc.headers or {}
    headers["X-Request-ID"] = req_id
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=headers,
    )


# Mount v1 API
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "api": settings.API_V1_STR,
    }


@app.get("/ready", tags=["Observability"])
def readiness_check():
    """
    Readiness probe for load balancers and orchestrators.
    Verifies that the database connection pool is active and operational.
    """
    try:
        with database.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "database": "connected",
        }
    except Exception as exc:
        logger.error("Readiness check failed: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "version": settings.VERSION,
                "environment": settings.ENVIRONMENT,
                "database": f"error: {str(exc)}",
            },
        )

