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
    await vector_service.ensure_collection()
    app.state.vector_service = vector_service
    
    async with db_manager.async_session_factory() as session:
        await seed_database(session, vector_service)
    
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

    @app_instance.get("/pay/{order_id}", response_class=HTMLResponse, include_in_schema=False)
    async def checkout_payment_page(order_id: str, session: AsyncSession = Depends(get_db)) -> HTMLResponse:
        """Serve responsive Razorpay payment checkout web page for end users."""
        from sqlalchemy import select
        from app.db.models import OrderModel, ProductModel, MerchantModel, PaymentModel
        from app.core.config import get_settings
        
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
        
        product_name = product.name if product else "Groceries"
        merchant_name = merchant.name if merchant else "Quick Commerce Hub"
        amount_inr = f"{order.total_amount / 100:.2f}"
        amount_paise = order.total_amount
        razorpay_order_id = payment.provider_ref if payment else f"order_{order.order_id[:14]}"
        key_id = cfg.RAZORPAY_KEY_ID
        is_paid = order.status in ("payment_success", "confirmed", "order_created", "completed")
        prep_time = getattr(product, "prep_time_minutes", 10) or 10

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pay ₹{amount_inr} • Transact AI Checkout</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }}
        body {{ background: #0b0f19; color: #f3f4f6; display: flex; align-items: center; justify-content: center; min-height: 100vh; padding: 20px; }}
        .card {{ background: #111827; border: 1px solid #1f2937; border-radius: 16px; max-width: 440px; width: 100%; padding: 28px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.5); }}
        .badge {{ display: inline-flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 600; padding: 4px 10px; border-radius: 20px; background: rgba(59,130,246,0.15); color: #60a5fa; margin-bottom: 16px; }}
        h1 {{ font-size: 20px; font-weight: 700; margin-bottom: 4px; color: #ffffff; }}
        .merchant {{ font-size: 13px; color: #9ca3af; margin-bottom: 20px; }}
        .details-box {{ background: #1f2937; border-radius: 12px; padding: 16px; margin-bottom: 24px; }}
        .row {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; font-size: 14px; }}
        .row:last-child {{ margin-bottom: 0; padding-top: 10px; border-top: 1px dashed #374151; font-weight: 700; font-size: 16px; }}
        .label {{ color: #9ca3af; }}
        .value {{ color: #f9fafb; }}
        .price {{ color: #34d399; }}
        .btn {{ width: 100%; background: #2563eb; color: #ffffff; border: none; padding: 14px 20px; font-size: 15px; font-weight: 600; border-radius: 10px; cursor: pointer; transition: all 0.2s; display: flex; align-items: center; justify-content: center; gap: 8px; }}
        .btn:hover {{ background: #1d4ed8; transform: translateY(-1px); }}
        .btn-test {{ background: transparent; border: 1px solid #374151; color: #9ca3af; margin-top: 12px; font-size: 13px; padding: 10px; }}
        .btn-test:hover {{ background: #1f2937; color: #f3f4f6; }}
        .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #6b7280; display: flex; align-items: center; justify-content: center; gap: 6px; }}
        .success-box {{ text-align: center; padding: 24px 10px; }}
        .success-icon {{ font-size: 48px; margin-bottom: 12px; }}
        .success-title {{ font-size: 22px; font-weight: 700; color: #10b981; margin-bottom: 8px; }}
    </style>
</head>
<body>
    <div class="card" id="checkout-card">
        {"<div class='success-box'><div class='success-icon'>✅</div><div class='success-title'>Order Already Paid!</div><p style='color:#9ca3af;font-size:14px;'>Your delivery of <strong>" + product_name + "</strong> is in transit (" + str(prep_time) + " min delivery).</p></div>" if is_paid else f'''
        <div class="badge">🔒 Razorpay Secure 256-Bit Checkout</div>
        <h1>{product_name}</h1>
        <div class="merchant">Sold by <strong>{merchant_name}</strong> • ⚡ {prep_time} min delivery</div>
        
        <div class="details-box">
            <div class="row"><span class="label">Quantity</span><span class="value">{order.quantity} unit</span></div>
            <div class="row"><span class="label">Delivery Location</span><span class="value">Pincode {order.pincode or '110001'}</span></div>
            <div class="row"><span class="label">Order ID</span><span class="value" style="font-family:monospace;font-size:12px;">{order_id[:8]}...{order_id[-4:]}</span></div>
            <div class="row"><span class="label">Total Amount</span><span class="value price">₹{amount_inr}</span></div>
        </div>

        <button class="btn" onclick="payNow()">
            <span>💳</span> Pay ₹{amount_inr} via Razorpay
        </button>

        <button class="btn btn-test" onclick="simulateTestPayment()">
            ⚡ Simulate Instant Test Payment (Mock Success)
        </button>

        <div class="footer">
            <span>🛡️</span> Powered by Transact AI • Razorpay Test Mode
        </div>
        '''}
    </div>

    <script>
        function payNow() {{
            var options = {{
                "key": "{key_id}",
                "amount": "{amount_paise}",
                "currency": "INR",
                "name": "Transact AI",
                "description": "{product_name}",
                "order_id": "{razorpay_order_id}",
                "handler": async function (response) {{
                    await handlePaymentSuccess(response.razorpay_order_id, response.razorpay_payment_id, response.razorpay_signature);
                }},
                "prefill": {{
                    "name": "Transact Shopper",
                    "email": "buyer@transact.ai",
                    "contact": "9876543210"
                }},
                "theme": {{ "color": "#2563eb" }}
            }};
            try {{
                var rzp = new Razorpay(options);
                rzp.open();
            }} catch(e) {{
                alert("Razorpay popup error: " + e.message);
            }}
        }}

        async function simulateTestPayment() {{
            await handlePaymentSuccess("{razorpay_order_id}", "pay_test_" + Math.random().toString(36).substring(7), "sig_test_mock");
        }}

        async function handlePaymentSuccess(rzpOrderId, rzpPayId, rzpSig) {{
            document.getElementById("checkout-card").innerHTML = `
                <div class="success-box">
                    <div class="success-icon">🎉</div>
                    <div class="success-title">Payment Successful!</div>
                    <p style="color:#d1d5db;font-size:14px;margin-bottom:12px;">Payment of <strong>₹{amount_inr}</strong> completed via Razorpay.</p>
                    <p style="color:#9ca3af;font-size:13px;">Order reference: <code style="color:#60a5fa;">${{rzpOrderId}}</code></p>
                    <div style="margin-top:20px;padding:12px;border-radius:8px;background:#1f2937;font-size:13px;color:#34d399;">
                        🚴 Partner assigned! Estimated delivery: <strong>{prep_time} minutes</strong>.
                    </div>
                </div>
            `;
        }}
    </script>
</body>
</html>"""
        return HTMLResponse(content=html_content)

    @app_instance.get("/", include_in_schema=False)
    async def root() -> RedirectResponse:
        """Redirect root to documentation."""
        return RedirectResponse(url="/docs")
        
    return app_instance


app = create_app()
