from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

from .routes import sync, webhooks
from ..config import settings


# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=settings.log_level,
)
logger.add(
    "logs/connector.log",
    rotation="500 MB",
    retention="10 days",
    level=settings.log_level,
)


# Create FastAPI application
app = FastAPI(
    title="WooCommerce <-> Odoo Connector",
    description="API for synchronizing data between WooCommerce and Odoo",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Application startup"""
    logger.info("Starting WooCommerce <-> Odoo Connector API")
    logger.info(f"WooCommerce URL: {settings.woo_url}")
    logger.info(f"Odoo URL: {settings.odoo_url}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    logger.info("Shutting down WooCommerce <-> Odoo Connector API")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "WooCommerce <-> Odoo Connector",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


# Include routers
app.include_router(sync.router, prefix="/sync", tags=["Sync"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "connector.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
