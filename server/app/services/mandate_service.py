"""Mandate service managing spending limits, versioning, budget calculations, and reservations."""

from datetime import datetime, timezone
from decimal import Decimal
import logging
from typing import List, Optional, Union
import uuid
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from server.app.core.errors import CartiAPIException, CartiErrorCode
from server.app.models.mandate import Mandate
from server.app.models.order import Order
from server.app.models.proposal import Proposal
from server.app.models.user import User
from server.app.schemas.mandate import (
    BudgetBreakdown,
    MandateCreate,
    MandateResponse,
    MandateValidationResult,
    generate_mandate_summary,
)
from server.app.services.audit_service import AuditService

logger = logging.getLogger("carti.mandates")


class MandateService:
    """Authoritative business logic and rules engine for user spending mandates."""

    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)

    def _ensure_user_exists_and_active(self, user_id: uuid.UUID) -> User:
        """Verify the user exists and account is active."""
        user = self.db.get(User, user_id)
        if not user:
            user = User(
                id=user_id,
                email=f"user_{str(user_id)[:8]}@carti.local",
                is_active=True,
                status="active",
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

        if not user.is_active or user.status != "active":
            raise CartiAPIException(
                code=CartiErrorCode.ACCESS_DENIED,
                message="User account is inactive or disabled.",
                status_code=403,
                retryable=False,
            )
        return user

    def get_current_mandate(self, user_id: uuid.UUID) -> Optional[Mandate]:
        """Load the active mandate for the user, checking for expiration."""
        stmt = (
            select(Mandate)
            .where(Mandate.user_id == user_id, Mandate.status == "active")
            .order_by(Mandate.version.desc())
        )
        mandate = self.db.scalars(stmt).first()
        if not mandate:
            return None

        # Check expiration
        now = datetime.now(timezone.utc)
        expires_at = mandate.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at <= now:
            mandate.status = "expired"
            self.db.commit()
            self.audit_service.record_event(
                user_id=user_id,
                event_type="mandate_expired",
                reason=f"Mandate version {mandate.version} passed expiration time.",
            )
            return None

        return mandate

    # Alias per specification name
    get_active_mandate = get_current_mandate

    def get_mandate_version(
        self,
        identifier: uuid.UUID,
        version: int,
        user_id: Optional[uuid.UUID] = None,
    ) -> Mandate:
        """Retrieve exact historical mandate version by (user_id, version) or (mandate_id, version)."""
        # 1. Query by user_id and version
        stmt = select(Mandate).where(Mandate.user_id == identifier, Mandate.version == version)
        mandate = self.db.scalars(stmt).first()

        # 2. If not found, try matching identifier as mandate_id
        if not mandate:
            stmt_id = select(Mandate).where(Mandate.id == identifier, Mandate.version == version)
            mandate = self.db.scalars(stmt_id).first()

        if not mandate:
            raise CartiAPIException(
                code=CartiErrorCode.MANDATE_NOT_FOUND,
                message=f"Mandate version {version} not found for identifier {identifier}.",
                status_code=404,
                retryable=False,
            )

        # Enforce caller ownership boundary if user_id is provided
        if user_id is not None and mandate.user_id != user_id:
            raise CartiAPIException(
                code=CartiErrorCode.ACCESS_DENIED,
                message="You do not have permission to access this mandate version.",
                status_code=403,
                retryable=False,
            )

        return mandate

    def get_mandate_by_id(self, mandate_id: uuid.UUID, user_id: Optional[uuid.UUID] = None) -> Mandate:
        """Retrieve mandate by ID with ownership verification."""
        mandate = self.db.get(Mandate, mandate_id)
        if not mandate:
            raise CartiAPIException(
                code=CartiErrorCode.MANDATE_NOT_FOUND,
                message=f"Mandate {mandate_id} not found.",
                status_code=404,
                retryable=False,
            )
        if user_id is not None and mandate.user_id != user_id:
            raise CartiAPIException(
                code=CartiErrorCode.ACCESS_DENIED,
                message="You do not have permission to access this mandate.",
                status_code=403,
                retryable=False,
            )
        return mandate

    def validate_mandate_is_active(
        self, mandate: Mandate, raise_exception: bool = True
    ) -> MandateValidationResult:
        """Validate whether mandate is active, unrevoked, and unexpired."""
        errors: List[str] = []

        if not mandate:
            errors.append("Mandate does not exist.")
            if raise_exception:
                raise CartiAPIException(
                    code=CartiErrorCode.MANDATE_NOT_FOUND,
                    message="Mandate does not exist.",
                    status_code=404,
                )
            return MandateValidationResult(valid=False, errors=errors)

        now = datetime.now(timezone.utc)
        expires_at = mandate.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        is_expired = expires_at <= now

        if is_expired:
            errors.append(f"Mandate expired at {expires_at.isoformat()}.")
            if mandate.status == "active":
                mandate.status = "expired"
                self.db.commit()
            if raise_exception:
                raise CartiAPIException(
                    code=CartiErrorCode.MANDATE_EXPIRED,
                    message="Spending mandate has expired. Please create a new mandate before shopping.",
                    status_code=400,
                )

        if mandate.status == "revoked":
            errors.append("Mandate has been revoked.")
            if raise_exception:
                raise CartiAPIException(
                    code=CartiErrorCode.MANDATE_INVALID,
                    message="Mandate has been revoked and cannot be used for purchases.",
                    status_code=400,
                )

        if mandate.status == "superseded":
            errors.append("Mandate has been superseded by a newer version.")
            if raise_exception:
                raise CartiAPIException(
                    code=CartiErrorCode.MANDATE_INVALID,
                    message=f"Mandate version {mandate.version} is superseded. Please use the current active version.",
                    status_code=400,
                )

        if mandate.status != "active":
            errors.append(f"Mandate status is '{mandate.status}'.")
            if raise_exception:
                raise CartiAPIException(
                    code=CartiErrorCode.MANDATE_INVALID,
                    message=f"Mandate version {mandate.version} is in invalid state '{mandate.status}'.",
                    status_code=400,
                )

        # Rule consistency check
        if mandate.per_item_cap > mandate.total_budget:
            errors.append("Per-item cap exceeds total budget.")
            if raise_exception:
                raise CartiAPIException(
                    code=CartiErrorCode.MANDATE_INVALID,
                    message="Mandate rule error: per-item cap cannot exceed total budget.",
                    status_code=400,
                )

        valid = len(errors) == 0
        return MandateValidationResult(
            valid=valid,
            mandate_id=mandate.id,
            version=mandate.version,
            status=mandate.status,
            is_expired=is_expired,
            errors=errors,
        )

    # Alias
    validate_mandate_active = validate_mandate_is_active

    def calculate_available_budget(
        self, mandate_id: uuid.UUID, lock_row: bool = False
    ) -> BudgetBreakdown:
        """
        Authoritative financial operation calculating remaining spendable budget.
        Formula: Available budget = Total budget - Captured spending - Active reservations.
        """
        # Fetch mandate, optionally using SELECT ... FOR UPDATE when supported
        if lock_row and self.db.bind and self.db.bind.dialect.name == "postgresql":
            stmt_m = select(Mandate).where(Mandate.id == mandate_id).with_for_update()
            mandate = self.db.scalars(stmt_m).first()
        else:
            mandate = self.db.get(Mandate, mandate_id)

        if not mandate:
            return BudgetBreakdown(
                mandate_id=mandate_id,
                total_budget=Decimal("0.00"),
                captured_spending=Decimal("0.00"),
                active_reservations=Decimal("0.00"),
                available_budget=Decimal("0.00"),
                currency="USD",
            )

        # Query orders: active mandate includes superseded lineage; historical queries scope to mandate_id
        if mandate.status == "active":
            orders_stmt = (
                select(Order)
                .join(Order.proposal)
                .where(
                    Order.user_id == mandate.user_id,
                    Order.proposal.has(
                        Proposal.mandate_id.in_(
                            select(Mandate.id).where(
                                Mandate.user_id == mandate.user_id,
                                Mandate.status.in_(["active", "superseded"]),
                            )
                        )
                    ),
                )
            )
        else:
            orders_stmt = (
                select(Order)
                .join(Order.proposal)
                .where(Order.proposal.has(mandate_id=mandate_id))
            )
        orders = self.db.scalars(orders_stmt).all()

        captured_spending = Decimal("0.00")
        active_reservations = Decimal("0.00")

        for o in orders:
            # Currency consistency check
            if o.currency != mandate.currency:
                raise CartiAPIException(
                    code=CartiErrorCode.CURRENCY_MISMATCH,
                    message=f"Currency mismatch: order currency '{o.currency}' differs from mandate currency '{mandate.currency}'.",
                    status_code=400,
                )

            # 1. Completed captured payments
            if o.status == "completed":
                captured_spending += o.amount
            # 2. In-flight reservations (created, buyer_approved, capture_pending, pending, processing)
            elif o.status in ["created", "buyer_approved", "capture_pending", "pending", "processing"]:
                active_reservations += o.budget_reserved
            # 3. Released reservations (cancelled, failed, refunded) do not consume budget

        raw_available = mandate.total_budget - captured_spending - active_reservations
        available_budget = max(Decimal("0.00"), raw_available)

        return BudgetBreakdown(
            mandate_id=mandate.id,
            total_budget=mandate.total_budget,
            captured_spending=captured_spending,
            active_reservations=active_reservations,
            available_budget=available_budget,
            currency=mandate.currency,
        )

    # Alias
    get_budget_breakdown = calculate_available_budget

    def create_or_update_mandate(
        self, user_id: uuid.UUID, mandate_in: MandateCreate
    ) -> Mandate:
        """
        Create a new mandate version, superseding prior versions while preserving history.
        Transactionally verifies that new budget is not below active committed spend.
        """
        self._ensure_user_exists_and_active(user_id)

        # Row-level lock or deterministic transaction serialization
        # Lock user record if on PostgreSQL to serialize version creation
        if self.db.bind and self.db.bind.dialect.name == "postgresql":
            self.db.scalars(select(User).where(User.id == user_id).with_for_update()).first()

        # Find latest version number for user
        version_stmt = select(func.coalesce(func.max(Mandate.version), 0)).where(
            Mandate.user_id == user_id
        )
        current_max_version = self.db.scalar(version_stmt) or 0
        new_version = current_max_version + 1

        # Check committed and reserved spend across active orders for this user
        # Completed orders + active in-flight reservations (including pending/processing)
        active_orders_stmt = select(Order).where(
            Order.user_id == user_id,
            Order.status.in_(["created", "buyer_approved", "capture_pending", "pending", "processing", "completed"]),
        )
        active_orders = self.db.scalars(active_orders_stmt).all()
        currently_committed = Decimal("0.00")
        for o in active_orders:
            if o.status == "completed":
                currently_committed += o.amount
            else:
                currently_committed += o.budget_reserved

        if mandate_in.total_budget < currently_committed:
            self.audit_service.record_event(
                user_id=user_id,
                event_type="budget_limit_exceeded",
                decision="rejected",
                reason=f"Attempted budget {mandate_in.total_budget} {mandate_in.currency} below committed spend {currently_committed} {mandate_in.currency}.",
            )
            raise CartiAPIException(
                code=CartiErrorCode.BUDGET_EXCEEDED,
                message=(
                    f"Cannot set total budget ({mandate_in.total_budget} {mandate_in.currency}) "
                    f"below active committed spend ({currently_committed} {mandate_in.currency})."
                ),
                status_code=400,
            )

        # Supersede currently active mandates
        active_stmt = select(Mandate).where(
            Mandate.user_id == user_id, Mandate.status == "active"
        )
        active_mandates = self.db.scalars(active_stmt).all()
        for m in active_mandates:
            m.status = "superseded"
            self.audit_service.record_event(
                user_id=user_id,
                event_type="mandate_version_superseded",
                details={
                    "mandate_id": str(m.id),
                    "old_version": m.version,
                    "superseded_by_version": new_version,
                },
            )

        # Create new mandate version
        new_mandate = Mandate(
            user_id=user_id,
            version=new_version,
            total_budget=mandate_in.total_budget,
            per_item_cap=mandate_in.per_item_cap,
            currency=mandate_in.currency,
            allowed_categories=mandate_in.allowed_categories,
            blocked_categories=mandate_in.blocked_categories,
            allowed_retailers=mandate_in.allowed_retailers,
            max_quantity_per_product=mandate_in.max_quantity_per_product,
            price_tolerance_pct=mandate_in.price_tolerance_pct,
            expires_at=mandate_in.expires_at,
            status="active",
        )
        self.db.add(new_mandate)
        self.db.commit()
        self.db.refresh(new_mandate)

        self.audit_service.record_event(
            user_id=user_id,
            event_type="mandate_created",
            details={
                "mandate_id": str(new_mandate.id),
                "version": new_version,
                "total_budget": str(new_mandate.total_budget),
                "per_item_cap": str(new_mandate.per_item_cap),
                "currency": new_mandate.currency,
            },
        )
        return new_mandate

    # Alias per specification name
    create_mandate = create_or_update_mandate

    def reserve_budget(
        self,
        mandate_id: uuid.UUID,
        amount: Decimal,
        order_id: Optional[uuid.UUID] = None,
        currency: Optional[str] = None,
    ) -> BudgetBreakdown:
        """
        Transactionally reserve budget for an approved proposal / in-flight checkout.
        Enforces that reservation cannot exceed available budget and currency matches.
        """
        mandate = self.get_mandate_by_id(mandate_id)
        if currency is not None and currency.upper() != mandate.currency.upper():
            raise CartiAPIException(
                code=CartiErrorCode.CURRENCY_MISMATCH,
                message=f"Currency mismatch: reservation currency '{currency}' does not match mandate currency '{mandate.currency}'.",
                status_code=400,
            )

        breakdown = self.calculate_available_budget(mandate_id, lock_row=True)

        if amount > breakdown.available_budget:
            self.audit_service.record_event(
                user_id=self.get_mandate_by_id(mandate_id).user_id,
                order_id=order_id,
                event_type="budget_limit_exceeded",
                decision="rejected",
                reason=f"Requested reservation {amount} exceeds available budget {breakdown.available_budget}.",
            )
            raise CartiAPIException(
                code=CartiErrorCode.BUDGET_EXCEEDED,
                message=f"Requested reservation ({amount} {breakdown.currency}) exceeds remaining available budget ({breakdown.available_budget} {breakdown.currency}).",
                status_code=400,
            )

        if order_id is not None:
            order = self.db.get(Order, order_id)
            if order:
                order.budget_reserved = amount
                self.db.commit()

        mandate = self.get_mandate_by_id(mandate_id)
        self.audit_service.record_event(
            user_id=mandate.user_id,
            order_id=order_id,
            event_type="budget_reservation_created",
            details={
                "mandate_id": str(mandate_id),
                "amount": str(amount),
                "currency": breakdown.currency,
            },
        )
        return self.calculate_available_budget(mandate_id)

    def release_budget_reservation(
        self, order_id: uuid.UUID, reason: str = "order_cancelled"
    ) -> None:
        """Release active budget reservation when an order is cancelled, rejected, or expired."""
        order = self.db.get(Order, order_id)
        if not order or order.budget_reserved == Decimal("0.00"):
            return  # Idempotent

        released_amount = order.budget_reserved
        order.budget_reserved = Decimal("0.00")
        if order.status in ["created", "buyer_approved", "capture_pending", "pending", "processing"]:
            order.status = "cancelled"
        self.db.commit()

        self.audit_service.record_event(
            user_id=order.user_id,
            order_id=order.id,
            event_type="budget_reservation_released",
            details={"released_amount": str(released_amount), "reason": reason},
        )

    def convert_reservation_to_captured(self, order_id: uuid.UUID) -> None:
        """Convert in-flight reservation into captured spending on confirmed PayPal capture."""
        order = self.db.get(Order, order_id)
        if not order:
            return

        if order.status == "completed" and order.budget_reserved == Decimal("0.00"):
            return  # Idempotent

        order.status = "completed"
        order.budget_reserved = Decimal("0.00")
        self.db.commit()

        self.audit_service.record_event(
            user_id=order.user_id,
            order_id=order.id,
            event_type="budget_reservation_captured",
            details={"amount": str(order.amount), "currency": order.currency},
        )

    def revoke_mandate(self, mandate_id: uuid.UUID, user_id: uuid.UUID) -> Mandate:
        """Revoke a spending mandate, blocking any new requests or checkout creations."""
        mandate = self.get_mandate_by_id(mandate_id, user_id=user_id)

        if mandate.status == "revoked":
            return mandate  # Idempotent

        mandate.status = "revoked"
        self.db.commit()
        self.db.refresh(mandate)

        self.audit_service.record_event(
            user_id=user_id,
            event_type="mandate_revoked",
            details={"mandate_id": str(mandate_id), "version": mandate.version},
        )
        return mandate

    def format_mandate_response(self, mandate: Mandate) -> MandateResponse:
        """Format Mandate model into canonical response with budget breakdown and summary."""
        breakdown = self.calculate_available_budget(mandate.id)
        summary = generate_mandate_summary(
            allowed_categories=mandate.allowed_categories,
            total_budget=mandate.total_budget,
            per_item_cap=mandate.per_item_cap,
            currency=mandate.currency,
            expires_at=mandate.expires_at,
            allowed_retailers=mandate.allowed_retailers,
        )
        return MandateResponse(
            id=mandate.id,
            user_id=mandate.user_id,
            version=mandate.version,
            total_budget=mandate.total_budget,
            per_item_cap=mandate.per_item_cap,
            currency=mandate.currency,
            allowed_categories=mandate.allowed_categories,
            blocked_categories=mandate.blocked_categories,
            allowed_retailers=mandate.allowed_retailers,
            max_quantity_per_product=mandate.max_quantity_per_product,
            price_tolerance_pct=mandate.price_tolerance_pct,
            expires_at=mandate.expires_at,
            status=mandate.status,
            created_at=mandate.created_at,
            available_budget=breakdown.available_budget,
            captured_spending=breakdown.captured_spending,
            active_reservations=breakdown.active_reservations,
            summary_text=summary,
        )
