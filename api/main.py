"""
FastAPI main application.
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import time
import os
from pathlib import Path

from api.v1.router import api_router
from api.core.config import settings
from apps.listings.reference_data import ensure_reference_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Village to Market - Connecting Zimbabwean farmers to markets",
    version="1.0.0",
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    openapi_url="/api/openapi.json" if settings.DEBUG else None,
)

cors_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:8001",
    "http://127.0.0.1:8001",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://villagetomarket.vercel.app",
]

if isinstance(settings.CORS_ALLOWED_ORIGINS, list):
    cors_origins.extend(settings.CORS_ALLOWED_ORIGINS)
elif isinstance(settings.CORS_ALLOWED_ORIGINS, str):
    cors_origins.append(settings.CORS_ALLOWED_ORIGINS)

cors_origins = list(set([o.strip().rstrip('/') for o in cors_origins]))

if "*" in cors_origins:
    cors_origins = ["*"]

# Trusted hosts middleware
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# CORS middleware MUST be added last so it becomes the outermost layer.
# This ensures it can attach CORS headers even if TrustedHostMiddleware rejects the request.
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True if "*" not in cors_origins else False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Request-ID"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add X-Process-Time header with request duration."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "details": exc.errors(),
            "status_code": 422,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "status_code": 500,
        },
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": "development" if settings.DEBUG else "production"
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Village to Market API",
        "version": "1.0.0",
        "docs": "/api/docs" if settings.DEBUG else "Docs disabled in production",
    }


# Include API routers
app.include_router(api_router, prefix="/api/v1")

# ── Serve uploaded media files (/media/*) ──────────────────────────────────
# Use Django's MEDIA_ROOT so we respect the Railway volume mount path
# (RAILWAY_VOLUME_MOUNT_PATH=/data → MEDIA_ROOT=/data/media) as well as the
# Cloudinary case.  When Cloudinary is active the images are served directly
# from the CDN so we still mount the local dir as a harmless fallback.
try:
    import django
    from django.conf import settings as _dj_settings
    _media_dir = Path(_dj_settings.MEDIA_ROOT)
except Exception:
    _media_dir = Path(__file__).resolve().parent.parent / "media"
_media_dir.mkdir(parents=True, exist_ok=True)   # ensure dir exists on fresh deploy
try:
    app.mount("/media", StaticFiles(directory=str(_media_dir)), name="media")
except Exception as _e:
    logger.warning("Could not mount /media static dir: %s", _e)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Actions to perform on startup."""
    logger.info("Starting Village to Market API...")
    logger.info(f"Environment: {'Development' if settings.DEBUG else 'Production'}")
    logger.info(f"Database: {settings.DATABASE_URL}")
    try:
        from channels.db import database_sync_to_async as sync_to_async

        categories_created, produce_created = await sync_to_async(ensure_reference_data)()
        logger.info(
            "Reference data ready: %s categories created, %s produce types created",
            categories_created,
            produce_created,
        )
    except Exception as exc:
        logger.warning("Reference data bootstrap skipped or failed: %s", exc)


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Actions to perform on shutdown."""
    logger.info("Shutting down Village to Market API...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )
