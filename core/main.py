from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import logging
import uvicorn

from core.config.settings import get_settings
from core.database.base import create_tables

# Importar modelos para que SQLAlchemy los reconozca
from ai_monitor.models.database import (
    ModelMetric, DriftDetection, Alert, DataQualityCheck, ModelPerformance
)

from ai_monitor.api.routes import router as monitor_router
from cost_optimizer.api.routes import router as optimizer_router
from compliance_guardian.api.routes import router as compliance_router

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("🚀 Starting AI Ops Suite...")
    
    # Create database tables
    try:
        create_tables()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise
    
    logger.info("✅ AI Ops Suite started successfully!")
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down AI Ops Suite...")


# Create FastAPI app
app = FastAPI(
    title="AI Ops Suite",
    description="Complementary tools for Scale AI ecosystem focusing on post-deployment optimization",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "modules": {
            "ai_monitor": settings.enable_real_time_alerts,
            "cost_optimizer": settings.enable_cost_optimizer,
            "compliance_guardian": settings.enable_compliance_guardian,
        }
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Ops Suite - Complementary tools for Scale AI",
        "docs": "/docs",
        "health": "/health",
        "version": "0.1.0",
        "modules": ["/monitor", "/optimizer", "/compliance"]
    }


# Include module routers
app.include_router(monitor_router, prefix="/monitor", tags=["AI Monitor"])
app.include_router(optimizer_router, prefix="/optimizer", tags=["Cost Optimizer"])
app.include_router(compliance_router, prefix="/compliance", tags=["Compliance Guardian"])


# Debug routes (only in development)
if settings.enable_debug_routes and settings.debug:
    @app.get("/debug/settings")
    async def debug_settings():
        """Debug endpoint to view current settings"""
        return {
            "database_url": settings.database_url.split("@")[-1],  # Hide credentials
            "redis_url": settings.redis_url,
            "debug": settings.debug,
            "feature_flags": {
                "cost_optimizer": settings.enable_cost_optimizer,
                "compliance_guardian": settings.enable_compliance_guardian,
                "real_time_alerts": settings.enable_real_time_alerts,
                "ml_predictions": settings.enable_ml_predictions,
            }
        }


if __name__ == "__main__":
    uvicorn.run(
        "core.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        workers=1 if settings.debug else settings.api_workers
    ) 