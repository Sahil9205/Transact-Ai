from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.v1 import api_v1_router
from app.core.config import get_settings
from app.core.exceptions import CommerceAgentError
from app.core.logging import get_logger, setup_logging
from app.core.security import validate_production_config
from app.db.database import get_database_manager, init_database_manager
from app.db.seed import seed_database
from app.services.vector_service import VectorService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for FastAPI app startup and shutdown."""
    settings = get_settings()
    
    setup_logging(log_level=settings.LOG_LEVEL, environment=settings.APP_ENV)
    logger = get_logger(__name__)
    
    if settings.APP_ENV.lower() == "production":
        validate_production_config(settings)
        
    db_manager = init_database_manager(settings.DATABASE_URL)
    await db_manager.init_db()
    
    vector_service = VectorService(
        qdrant_url=settings.QDRANT_URL,
        qdrant_api_key=settings.QDRANT_API_KEY,
        collection_name=settings.QDRANT_COLLECTION,
    )
    await vector_service.ensure_collection()
    app.state.vector_service = vector_service
    
    async for session in db_manager.get_session():
        await seed_database(session, vector_service)
        break
    
    logger.info("Starting up application", env=settings.APP_ENV, version=settings.APP_VERSION)
    
    yield
    
    logger.info("Shutting down application")
    await db_manager.close()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    
    app_instance = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Transact AI — Provider-independent AI Commerce Agent API",
        lifespan=lifespan,
    )
    
    app_instance.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    from app.api.v1.mcp import router as mcp_router
    app_instance.include_router(health_router)
    app_instance.include_router(mcp_router)
    app_instance.include_router(api_v1_router)
    
    @app_instance.exception_handler(CommerceAgentError)
    async def commerce_agent_error_handler(request: Request, exc: CommerceAgentError) -> JSONResponse:
        """Handle custom CommerceAgentError."""
        return JSONResponse(
            status_code=400,
            content={
                "error_code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
        )
        
    @app_instance.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle generic unhandled exceptions."""
        logger = get_logger(__name__)
        logger.error("Unhandled exception", error=str(exc))
        return JSONResponse(
            status_code=500,
            content={"error_code": "INTERNAL_ERROR", "message": "An unexpected error occurred."},
        )
        
    @app_instance.get("/.well-known/ai-plugin.json", include_in_schema=False)
    async def get_ai_plugin_manifest() -> FileResponse:
        """Serve ChatGPT Plugin Manifest."""
        from pathlib import Path
        path = Path(__file__).parent.parent / ".well-known" / "ai-plugin.json"
        return FileResponse(path, media_type="application/json")

    @app_instance.get("/.well-known/openapi.json", include_in_schema=False)
    async def get_plugin_openapi() -> FileResponse:
        """Serve Plugin OpenAPI Specification."""
        from pathlib import Path
        path = Path(__file__).parent.parent / ".well-known" / "openapi.json"
        return FileResponse(path, media_type="application/json")

    @app_instance.get("/.well-known/gemini-extension.json", include_in_schema=False)
    async def get_gemini_extension_manifest() -> FileResponse:
        """Serve Google Gemini Extension Manifest."""
        from pathlib import Path
        path = Path(__file__).parent.parent / ".well-known" / "gemini-extension.json"
        return FileResponse(path, media_type="application/json")

    @app_instance.get("/", include_in_schema=False)
    async def root() -> RedirectResponse:
        """Redirect root to documentation."""
        return RedirectResponse(url="/docs")
        
    return app_instance


app = create_app()
