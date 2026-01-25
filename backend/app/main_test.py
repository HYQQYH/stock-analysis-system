"""FastAPI Main Application - Test Version (Simplified)"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

# Configure logging
logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Stock Analysis System API",
    description="A comprehensive stock analysis platform with AI-powered insights",
    version="v1",
    debug=True
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API information"""
    return {
        "name": "Stock Analysis System API",
        "version": "v1",
        "environment": "development",
        "status": "running"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": "development",
        "api_version": "v1"
    }


@app.get("/docs", tags=["Documentation"])
async def swagger_docs():
    """Swagger UI documentation"""
    return {
        "message": "Swagger UI available at /docs",
        "redoc": "ReDoc available at /redoc"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
