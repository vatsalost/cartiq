"""Authentication and session lifecycle service."""

from datetime import datetime, timedelta, timezone
import hashlib
import logging
import secrets
from typing import Optional, Tuple
import uuid
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy import select
from sqlalchemy.orm import Session
from server.app.core.config import settings
from server.app.core.errors import CartiAPIException, CartiErrorCode
from server.app.models.session import UserSession
from server.app.models.user import User
from server.app.schemas.auth import UserSafeProfile
from server.app.services.audit_service import AuditService

logger = logging.getLogger("carti.auth")
password_hasher = PasswordHasher()


class AuthService:
    """Handles password hashing, user registration, login, and session revocation."""

    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using Argon2id."""
        return password_hasher.hash(password)

    @staticmethod
    def verify_password(hash_str: str, plain_password: str) -> bool:
        """Verify password against Argon2id hash with constant-time comparison."""
        try:
            return password_hasher.verify(hash_str, plain_password)
        except VerifyMismatchError:
            return False
        except Exception:
            return False

    @staticmethod
    def hash_token(raw_token: str) -> str:
        """Hash raw session token using SHA-256 for secure database storage."""
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    def _create_session(
        self, user_id: uuid.UUID, ip_address: Optional[str] = None, user_agent: Optional[str] = None
    ) -> Tuple[str, UserSession]:
        """Generate a cryptographically secure token and persist its hash in user_sessions."""
        raw_token = secrets.token_urlsafe(32)
        token_hash = self.hash_token(raw_token)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=settings.SESSION_EXPIRE_DAYS)

        session = UserSession(
            user_id=user_id,
            token_hash=token_hash,
            created_at=now,
            expires_at=expires_at,
            last_activity_at=now,
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else None,
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return (raw_token, session)

    def register_user(
        self,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[User, str, UserSession]:
        """Register a new user account with Argon2id password hash."""
        clean_email = email.strip().lower()

        # Check existing user
        existing = self.db.scalars(select(User).where(User.email == clean_email)).first()
        if existing:
            raise CartiAPIException(
                code=CartiErrorCode.VALIDATION_ERROR,
                message="An account with this email address already exists.",
                status_code=409,
            )

        hashed_pw = self.hash_password(password)
        user = User(
            email=clean_email,
            password_hash=hashed_pw,
            is_active=True,
            status="active",
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        raw_token, session = self._create_session(user.id, ip_address, user_agent)

        self.audit_service.record_event(
            user_id=user.id,
            event_type="user_registered",
            details={"email": clean_email, "ip": ip_address},
        )
        return (user, raw_token, session)

    def login_user(
        self,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[User, str, UserSession]:
        """Authenticate user with email and password, rotating to a fresh session."""
        clean_email = email.strip().lower()
        user = self.db.scalars(select(User).where(User.email == clean_email)).first()

        # Constant-time verify failure to prevent user enumeration
        dummy_hash = (
            "$argon2id$v=19$m=65536,t=3,p=4$wGj158CHlJNLGY4XF6Y79Q$uahY+O2MoNdxKhQbJWiPfmZEawY6IRI54X2HF76njRg"
        )
        if not user or not user.password_hash:
            self.verify_password(dummy_hash, password)
            raise CartiAPIException(
                code=CartiErrorCode.AUTHENTICATION_REQUIRED,
                message="Invalid email or password.",
                status_code=401,
            )

        if not self.verify_password(user.password_hash, password):
            raise CartiAPIException(
                code=CartiErrorCode.AUTHENTICATION_REQUIRED,
                message="Invalid email or password.",
                status_code=401,
            )

        if not user.is_active or user.status != "active":
            raise CartiAPIException(
                code=CartiErrorCode.ACCESS_DENIED,
                message="Account is disabled or inactive. Please contact support.",
                status_code=403,
            )

        # Session rotation: Issue brand new session token
        raw_token, session = self._create_session(user.id, ip_address, user_agent)

        self.audit_service.record_event(
            user_id=user.id,
            event_type="user_logged_in",
            details={"email": clean_email, "ip": ip_address},
        )
        return (user, raw_token, session)

    def login_demo_user(
        self,
        demo_identifier: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[User, str, UserSession]:
        """Create or authenticate an isolated demo user for local development."""
        if not settings.is_demo_allowed():
            raise CartiAPIException(
                code=CartiErrorCode.ACCESS_DENIED,
                message="Demo authentication is disabled in this environment.",
                status_code=403,
            )

        # Isolated identity per demo identifier
        if demo_identifier:
            safe_id = hashlib.sha256(demo_identifier.encode("utf-8")).hexdigest()[:8]
            demo_email = f"demo_{safe_id}@carti.local"
        else:
            demo_email = settings.DEMO_USER_EMAIL

        user = self.db.scalars(select(User).where(User.email == demo_email)).first()
        if not user:
            # Seed demo user
            user_id = uuid.UUID(settings.DEMO_USER_ID) if demo_email == settings.DEMO_USER_EMAIL else uuid.uuid4()
            user = User(
                id=user_id,
                email=demo_email,
                is_active=True,
                status="active",
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

        raw_token, session = self._create_session(user.id, ip_address, user_agent)
        return (user, raw_token, session)

    def logout_session(self, raw_token: Optional[str]) -> bool:
        """Revoke active session in database."""
        if not raw_token:
            return True

        token_hash = self.hash_token(raw_token)
        session = self.db.scalars(
            select(UserSession).where(UserSession.token_hash == token_hash)
        ).first()

        if session and session.revoked_at is None:
            session.revoked_at = datetime.now(timezone.utc)
            self.db.commit()
            self.audit_service.record_event(
                user_id=session.user_id,
                event_type="user_logged_out",
                details={"session_id": str(session.id)},
            )
        return True

    def validate_session_token(self, raw_token: str) -> Optional[User]:
        """Validate session token against database. Checks expiration and revocation."""
        if not raw_token:
            return None

        token_hash = self.hash_token(raw_token)
        session = self.db.scalars(
            select(UserSession).where(UserSession.token_hash == token_hash)
        ).first()

        if not session:
            return None

        # Check revocation
        if session.revoked_at is not None:
            return None

        # Check expiration
        now = datetime.now(timezone.utc)
        expires_at = session.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= now:
            return None

        # Check user status
        user = session.user
        if not user or not user.is_active or user.status != "active":
            return None

        # Update last activity
        session.last_activity_at = now
        self.db.commit()
        return user
