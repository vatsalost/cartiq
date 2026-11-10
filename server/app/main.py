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

                # Auto-seed default proposal for demo review & checkout
                from server.app.models.candidate import Candidate, CandidateOffer
                from server.app.models.proposal import Proposal
                from server.app.models.request import ShoppingRequest

                prop_uuid = uuid.UUID("98765432-1111-2222-3333-444455556666")
                demo_prop = db.get(Proposal, prop_uuid)
                effective_mandate = active_mandate or new_mandate
                if not demo_prop:
                    demo_req = db.scalars(select(ShoppingRequest).where(ShoppingRequest.user_id == demo_uuid)).first()
                    if not demo_req:
                        demo_req = ShoppingRequest(
                            id=uuid.uuid4(),
                            user_id=demo_uuid,
                            mandate_id=effective_mandate.id,
                            raw_prompt="Ergonomic wireless mouse",
                            status="proposal_ready",
                        )
                        db.add(demo_req)
                        db.flush()

                    demo_cand = db.scalars(select(Candidate).where(Candidate.request_id == demo_req.id)).first()
                    if not demo_cand:
                        demo_cand = Candidate(
                            id=uuid.uuid4(),
                            request_id=demo_req.id,
                            provider_product_id="prod_logi_mx_master_3s",
                            title="Logitech MX Master 3S Wireless Performance Mouse",
                            brand="Logitech",
                            category="Electronics",
                            image_url="https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=600&auto=format&fit=crop&q=80",
                        )
                        db.add(demo_cand)
                        db.flush()

                    demo_offer = db.scalars(select(CandidateOffer).where(CandidateOffer.candidate_id == demo_cand.id)).first()
                    if not demo_offer:
                        demo_offer = CandidateOffer(
                            id=uuid.uuid4(),
                            candidate_id=demo_cand.id,
                            provider_offer_id="off_target_mx_3s",
                            domain="target.com",
                            buy_url="https://www.target.com/p/logitech-mx-master-3s",
                            price_amount=Decimal("49.99"),
                            currency="USD",
                            availability="InStock",
                            condition="new",
                            is_eligible=True,
                        )
                        db.add(demo_offer)
                        db.flush()

                    now = datetime.now(timezone.utc)
                    demo_prop = Proposal(
                        id=prop_uuid,
                        request_id=demo_req.id,
                        user_id=demo_uuid,
                        mandate_id=effective_mandate.id,
                        mandate_version=effective_mandate.version,
                        candidate_id=demo_cand.id,
                        offer_id=demo_offer.id,
                        quantity=1,
                        unit_price_at_proposal=Decimal("49.99"),
                        subtotal_at_proposal=Decimal("49.99"),
                        shipping_amount=Decimal("0.00"),
                        tax_amount=Decimal("0.00"),
                        total_amount=Decimal("49.99"),
                        currency="USD",
                        rationale="Selected best match adhering to mandate spending policy.",
                        guardrail_result={"status": "passed", "verdict": "compliant"},
                        verification_result={"valid": True},
                        verification_status="verified",
                        status="pending",
                        expires_at=now + timedelta(days=90),
                    )
                    db.add(demo_prop)
                    db.commit()
                    logger.info("Seeded initial proposal for demo user %s.", demo_uuid)
                elif demo_prop.status in ["checkout_started", "expired"]:
                    demo_prop.status = "pending"
                    demo_prop.expires_at = datetime.now(timezone.utc) + timedelta(days=90)
                    db.commit()
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
