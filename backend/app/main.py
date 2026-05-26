"""
PlantDiseaseAI — FastAPI Application Entry Point

Initializes the app, registers routes, connects services on startup.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.utils.redis_client import redis_client
from app.utils.minio_client import minio_client
from app.services.ml_service import ml_service
from app.routers import auth, predict, history, crops

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events.
    - Startup: Connect Redis, MinIO, load ML model
    - Shutdown: Disconnect Redis
    """
    # ── Startup ──
    print("🚀 Starting PlantDiseaseAI backend...")

    # Connect Redis
    await redis_client.connect()
    print("✅ Redis connected")

    # Connect MinIO
    minio_client.connect()
    print("✅ MinIO connected")

    # Load ML model
    ml_service.load_model()
    print("✅ ML model loaded")

    print(f"🌿 PlantDiseaseAI v{settings.APP_VERSION} is ready!")

    yield  # App is running

    # ── Shutdown ──
    print("🛑 Shutting down...")
    await redis_client.disconnect()
    print("✅ Redis disconnected")


# ── Create FastAPI App ──
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered plant disease identification API",
    lifespan=lifespan,
)

# ── CORS Middleware (allow Flutter app requests) ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register Routers ──
app.include_router(auth.router)
app.include_router(predict.router)
app.include_router(history.router)
app.include_router(crops.router)


# ── Health Check ──
@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }
