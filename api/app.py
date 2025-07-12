import sys
import os
import uvicorn

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
import cv2
import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.router.api import router


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""

    app = FastAPI(
        title="Comic Translate API",
        description="API for translating comic images",
        version="1.0.0",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(router)

    @app.get("/")
    async def root():
        return {"message": "Comic Translate API is running"}

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    return app
