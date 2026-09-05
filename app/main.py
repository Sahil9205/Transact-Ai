from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import Depends, FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import get_db

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
    try:
        await vector_service.ensure_collection()
        app.state.vector_service = vector_service
        async with db_manager.async_session_factory() as session:
            await seed_database(session, vector_service)
    except Exception as e:
        logger.warning(f"Qdrant Cloud network warning during startup: {e}")
        app.state.vector_service = vector_service
    
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
    from app.api.v1.products import router as products_router
    app_instance.include_router(health_router)
    app_instance.include_router(mcp_router)
    app_instance.include_router(products_router)
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

    @app_instance.get("/favicon.ico", include_in_schema=False)
    @app_instance.get("/favicon.png", include_in_schema=False)
    async def get_favicon() -> FileResponse:
        """Serve TransactAI favicon."""
        from pathlib import Path
        path = Path(__file__).parent.parent / "frontend" / "favicon.png"
        return FileResponse(path, media_type="image/png")

    @app_instance.get("/logo_icon.png", include_in_schema=False)
    @app_instance.get("/logo.png", include_in_schema=False)
    async def get_logo_icon() -> FileResponse:
        """Serve TransactAI logo icon."""
        from pathlib import Path
        path = Path(__file__).parent.parent / "frontend" / "logo_icon.png"
        return FileResponse(path, media_type="image/png")

    @app_instance.get("/logo_full.png", include_in_schema=False)
    async def get_logo_full() -> FileResponse:
        """Serve TransactAI full brand logo lockup."""
        from pathlib import Path
        path = Path(__file__).parent.parent / "frontend" / "logo_full.png"
        return FileResponse(path, media_type="image/png")

    @app_instance.get("/pay/{order_id}", response_class=HTMLResponse, include_in_schema=False)
    async def checkout_payment_page(order_id: str, session: AsyncSession = Depends(get_db)) -> HTMLResponse:
        """Serve responsive Razorpay payment checkout web page for end users."""
        from sqlalchemy import select
        from app.db.models import OrderModel, ProductModel, MerchantModel, PaymentModel
        from app.core.config import get_settings
        from app.services.frontend_service import FrontendService
        
        cfg = get_settings()
        stmt = select(OrderModel).where(OrderModel.order_id == order_id)
        res = await session.execute(stmt)
        order = res.scalar_one_or_none()
        if not order:
            return HTMLResponse(
                content="<h2 style='font-family:sans-serif;text-align:center;margin-top:50px;color:#ef4444;'>Order not found</h2>",
                status_code=404,
            )
            
        stmt_p = select(ProductModel).where(ProductModel.product_id == order.product_id)
        res_p = await session.execute(stmt_p)
        product = res_p.scalar_one_or_none()
        
        stmt_m = select(MerchantModel).where(MerchantModel.merchant_id == order.merchant_id)
        res_m = await session.execute(stmt_m)
        merchant = res_m.scalar_one_or_none()
        
        stmt_pay = select(PaymentModel).where(PaymentModel.order_id == order_id)
        res_pay = await session.execute(stmt_pay)
        payment = res_pay.scalar_one_or_none()
        
        html_content = FrontendService.render_checkout_page(order, product, merchant, payment, cfg)
        return HTMLResponse(content=html_content)

    @app_instance.get("/merchant/register", response_class=HTMLResponse, include_in_schema=False)
    async def merchant_register_page() -> HTMLResponse:
        """Serve clean, light-mode merchant self-service registration portal."""
        from app.services.frontend_service import FrontendService
        return HTMLResponse(content=FrontendService.render_register_page())

    @app_instance.get("/merchant/dashboard", response_class=HTMLResponse, include_in_schema=False)
    async def merchant_dashboard_redirect(session: AsyncSession = Depends(get_db)):
        """Redirects to the first active merchant dashboard or the registration page."""
        from app.services.merchant_service import MerchantService
        merchants = await MerchantService.list_merchants(session)
        if merchants:
            return RedirectResponse(url=f"/merchant/dashboard/{merchants[0].provider_id}")
        return RedirectResponse(url="/merchant/register")

    @app_instance.get("/merchant/dashboard/{merchant_id}", response_class=HTMLResponse, include_in_schema=False)
    async def merchant_dashboard_page(merchant_id: str, session: AsyncSession = Depends(get_db)) -> HTMLResponse:
        """Serve clean, light-mode interactive merchant dashboard."""
        from app.services.merchant_service import MerchantService
        from app.services.frontend_service import FrontendService
        try:
            stats = await MerchantService.get_dashboard_stats(session, merchant_id)
            all_merchants = await MerchantService.list_merchants(session)
            merchants_list = [m.model_dump(mode="json") for m in all_merchants]
            html = FrontendService.render_dashboard_page(
                merchant_data=stats["merchant"].model_dump(mode="json"),
                stats=stats,
                all_merchants=merchants_list,
            )
            return HTMLResponse(content=html)
        except Exception as e:
            return HTMLResponse(
                content=f"<div style='font-family:sans-serif;text-align:center;padding:50px;'><h2>Merchant not found</h2><p style='color:#64748b;'>{str(e)}</p><a href='/merchant/register'>Register New Merchant</a></div>",
                status_code=404,
            )

    @app_instance.get("/merchant", response_class=HTMLResponse, include_in_schema=False)
    @app_instance.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def merchant_gateway_landing(session: AsyncSession = Depends(get_db)) -> HTMLResponse:
        """Serve merchant partner gateway landing page to choose existing or new store."""
        from app.services.merchant_service import MerchantService
        from app.services.frontend_service import FrontendService
        all_merchants = await MerchantService.list_merchants(session)
        merchants_list = [m.model_dump(mode="json") for m in all_merchants]
        html = FrontendService.render_landing_page(merchants_list)
        return HTMLResponse(content=html)
        
    return app_instance


app = create_app()
