"""FastAPI application factory and lifespan management.

Creates the FastAPI app, configures middleware, loads ML models on startup,
and registers all routes. This is the entry point for uvicorn.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.websocket import init_shared_resources, router as ws_router
from app.config import get_settings
from app.core.frame_processor import FrameProcessor
from app.core.llm_service import LLMService
from app.core.sign_classifier import SignClassifier
from app.utils.logging import get_logger, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — initialise resources on startup, cleanup on shutdown."""
    settings = get_settings()
    logger = setup_logging(settings.log_level)
    log = get_logger("main")

    log.info("Starting ISL Translator Backend...")

    # Load ML models
    log.info("Loading frame processor (MediaPipe)...")
    frame_processor = FrameProcessor()

    log.info("Loading sign classifier (TFLite)...")
    sign_classifier = SignClassifier(
        model_path=settings.model_path,
        labels_path=settings.labels_path,
    )

    log.info("Initialising LLM service (Groq)...")
    llm_service = LLMService(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
    )

    # Inject shared resources into WebSocket handler
    init_shared_resources(frame_processor, sign_classifier, llm_service)

    log.info(
        "Backend ready — model: %s, classes: %d",
        settings.model_path,
        sign_classifier.num_classes,
    )

    yield

    # Shutdown
    log.info("Shutting down...")
    frame_processor.close()
    await llm_service.close()
    log.info("Shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="ISL Translator API",
        description="Indian Sign Language → Text → Sentences",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    app.include_router(ws_router)

    @app.get("/health", tags=["health"])
    async def health_check():
        """Health check endpoint for load balancers and container orchestrators."""
        return {
            "status": "healthy",
            "service": "isl-translator-backend",
            "version": "1.0.0",
        }

    return app


# Uvicorn entry point
app = create_app()
