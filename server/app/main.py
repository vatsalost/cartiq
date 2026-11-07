"""Main entrypoint for Carti Backend FastAPI Application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from server.app.api.routes import (
    auth_router,
    audit_router,
    health_router,
    mandates_router,
    orders_router,
    proposals_router,
    requests_router,
    webhooks_router,
)
from server.app.core.config import settings
from server.app.core.errors import (
    CartiAPIException,
    CartiErrorCode,
    carti_exception_handler,
    generic_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from server.app.core.logging import logger, setup_logging
from server.app.db.session import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for initialization and shutdown."""
    setup_logging()
    logger.info("Initializing Carti Backend (%s)...", settings.APP_ENV)

    # In development/test mode, ensure database tables exist
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema validated successfully.")
    except Exception as exc:
        logger.warning("Could not auto-create tables on startup: %s", exc)

    # Auto-seed default spending mandate for demo user if none exists
    if settings.is_demo_allowed():
        try:
            import uuid
            from datetime import datetime, timedelta, timezone
            from decimal import Decimal
            from sqlalchemy import select
            from server.app.db.session import SessionLocal
            from server.app.models.mandate import Mandate
            from server.app.models.user import User

            demo_uuid = uuid.UUID(settings.DEMO_USER_ID)
            with SessionLocal() as db:
                user = db.get(User, demo_uuid)
                if not user:
                    user = User(
                        id=demo_uuid,
                        email=settings.DEMO_USER_EMAIL,
                        is_active=True,
                        status="active",
                    )
                    db.add(user)
                    db.commit()

                active_mandate = db.scalars(
                    select(Mandate).where(Mandate.user_id == demo_uuid, Mandate.status == "active")
                ).first()
                if not active_mandate:
                    now = datetime.now(timezone.utc)
                    new_mandate = Mandate(
                        user_id=demo_uuid,
                        version=1,
                        status="active",
                        total_budget=Decimal("150.00"),
                        per_item_cap=Decimal("60.00"),
                        currency="USD",
                        allowed_categories=["Lighting", "Kitchen", "Electronics", "Home Office"],
                        blocked_categories=[],
                        allowed_retailers=["amazon.com", "target.com", "bestbuy.com"],
                        max_quantity_per_product=2,
                        price_tolerance_pct=Decimal("0.1000"),
                        expires_at=now + timedelta(days=90),
                    )
                    db.add(new_mandate)
                    db.commit()
                    logger.info("Seeded initial spending mandate v1 for demo user %s.", demo_uuid)
        except Exception as exc:
            logger.warning("Could not auto-seed demo mandate: %s", exc)

    yield

    logger.info("Shutting down Carti Backend.")


# Initialize FastAPI app with comprehensive OpenAPI documentation
app = FastAPI(
    title="Carti — Agentic Shopping Concierge API",
    version=settings.APP_VERSION,
    description=(
        "Carti is an AI shopping concierge built for the PayPal AI Hackathon 2026. "
        "The server enforces deterministic spending mandates, product validation, "
        "and secure PayPal Orders v2 Sandbox payments."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "User registration, session login, logout, and status checks.",
        },
        {
            "name": "Health",
            "description": "System health and database connectivity checks.",
        },
        {
            "name": "Mandates",
            "description": "Spending mandate creation, versioning, and limits.",
        },
        {
            "name": "Requests",
            "description": "Natural-language shopping requests, progress SSE, and cancellation.",
        },
        {
            "name": "Proposals",
            "description": "Purchase proposal reviews and PayPal order creation requests.",
        },
        {
            "name": "Orders",
            "description": "PayPal payment captures, full refunds, and order history.",
        },
        {
            "name": "Webhooks",
            "description": "PayPal asynchronous event verification and state reconciliation.",
        },
    ],
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request body size limiter middleware
@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > settings.MAX_REQUEST_BODY_BYTES:
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={
                        "error": {
                            "code": CartiErrorCode.VALIDATION_ERROR,
                            "message": f"Request body exceeds maximum allowed limit of {settings.MAX_REQUEST_BODY_BYTES} bytes.",
                            "retryable": False,
                            "details": {},
                        }
                    },
                )
        except ValueError:
            pass
    return await call_next(request)


# Register centralized exception handlers
app.add_exception_handler(CartiAPIException, carti_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Mount API routers under /api
app.include_router(auth_router, prefix="/api")
app.include_router(audit_router, prefix="/api")
app.include_router(health_router, prefix="/api")
app.include_router(mandates_router, prefix="/api")
app.include_router(requests_router, prefix="/api")
app.include_router(proposals_router, prefix="/api")
app.include_router(orders_router, prefix="/api")
app.include_router(webhooks_router, prefix="/api")
