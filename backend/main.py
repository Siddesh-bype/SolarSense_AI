"""
SolarSense AI — FastAPI Backend Entry Point
"""
import logging
import os
import sys
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("solarsense")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logger.info("=" * 60)
    logger.info("  SolarSense AI — Starting up...")
    logger.info("=" * 60)

    # Log GPU info
    try:
        from backend.utils.gpu_manager import get_device_info
        info = get_device_info()
        logger.info(f"  Device: {info['device']}")
        logger.info(f"  PyTorch: {info['torch_version']}")
        if info.get("gpu_name"):
            logger.info(f"  GPU: {info['gpu_name']} ({info.get('gpu_memory_gb', '?')} GB)")
    except Exception as e:
        logger.warning(f"  GPU detection failed: {e}")

    # Ensure output directories exist
    os.makedirs("scan_outputs", exist_ok=True)
    os.makedirs("debug_outputs", exist_ok=True)

    logger.info("  Ready to accept requests!")
    logger.info("=" * 60)
    yield
    # Shutdown
    logger.info("SolarSense AI — Shutting down.")


# Create FastAPI app
app = FastAPI(
    title="SolarSense AI",
    description="AI-powered rooftop solar planning tool for Indian homeowners",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow all origins for hackathon demo
cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000",
)
allowed_origins = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for scan outputs
os.makedirs("scan_outputs", exist_ok=True)
app.mount("/static", StaticFiles(directory="scan_outputs"), name="static")

# Import and include routers
from backend.routers.scan import router as scan_router
from backend.routers.financial import router as financial_router

app.include_router(scan_router, prefix="/api/scan", tags=["scan"])
app.include_router(financial_router, prefix="/api/financial", tags=["financial"])


@app.get("/")
async def root():
    return {
        "name": "SolarSense AI",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}
