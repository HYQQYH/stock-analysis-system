"""FastAPI Main Application"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.config import settings
import logging
from app.tasks import start_scheduler, stop_scheduler
# from app.api import tasks as tasks_api
from app.api import stocks as stocks_api
from app.api import market as market_api
from app.api import analysis as analysis_api
from app.api import asserts as asserts_api

# Configure logging
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info("Application starting up...")
    try:
        start_scheduler()
        logger.info("Background scheduler started during startup")
    except Exception:
        logger.exception("Failed to start scheduler on startup")
    yield
    # Shutdown
    logger.info("Application shutting down...")
    try:
        stop_scheduler()
        logger.info("Background scheduler stopped during shutdown")
    except Exception:
        logger.exception("Failed to stop scheduler on shutdown")


# Create FastAPI application
app = FastAPI(
    title="Stock Analysis System API",
    description="A comprehensive stock analysis platform with AI-powered insights",
    version=settings.api_version,
    debug=settings.debug,
    # lifespan=lifespan
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API information"""
    return {
        "name": "Stock Analysis System API",
        "version": settings.api_version,
        "environment": settings.environment,
        "status": "running"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.environment
    }


@app.get("/docs", tags=["Documentation"])
async def swagger_ui():
    """Swagger UI documentation"""
    return {"message": "Swagger UI available at /docs"}


@app.get("/api/{version}/health", tags=["Health"])
async def api_health_check(version: str):
    """API version-specific health check"""
    if version != settings.api_version:
        return JSONResponse(
            status_code=400,
            content={"error": f"API version {version} not supported"}
        )
    return {
        "status": "healthy",
        "version": version,
        "timestamp": __import__("datetime").datetime.now().isoformat()
    }


# Error handlers
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )


# Include routers
app.include_router(stocks_api.router, prefix="/api/v1", tags=["stocks"])
app.include_router(market_api.router, prefix="/api/v1", tags=["market"])
app.include_router(analysis_api.router, prefix="/api/v1", tags=["analysis"])
app.include_router(asserts_api.router, prefix="/api/v1", tags=["asserts"])
# app.include_router(tasks_api.router, prefix="/api/v1/tasks", tags=["tasks"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
