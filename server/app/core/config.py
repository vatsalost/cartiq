"""Application configuration for Carti Backend."""

from typing import List
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Carti application settings loaded from environment or .env file."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application settings
    APP_NAME: str = "Carti API"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    APP_BASE_URL: str = "http://localhost:8000"
    CLIENT_BASE_URL: str = "http://localhost:5173"

    # Database
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/carti_db"
    SQLITE_FALLBACK: bool = True
    DB_ECHO: bool = False

    # LLM Settings
    LLM_PROVIDER: str = "gemini"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gemini-2.5-flash"
    LLM_TEMPERATURE: float = 0.2
    LLM_TIMEOUT_SECONDS: float = 15.0
    LLM_MAX_TOKENS: int = 2048

    # Agent Loop & Tool Gateway Settings
    AGENT_MAX_ITERATIONS: int = 8
    AGENT_MAX_TOOL_CALLS: int = 6
    AGENT_MAX_SEARCH_CALLS: int = 4
    AGENT_MAX_EXECUTION_SECONDS: float = 30.0
    AGENT_MAX_CANDIDATES: int = 30
    TOOL_DEFAULT_TIMEOUT_SECONDS: float = 5.0

    # Channel3 Settings
    CHANNEL3_API_KEY: str = ""
    CHANNEL3_BASE_URL: str = "https://api.trychannel3.com/v1"
    CHANNEL3_COUNTRY: str = "US"
    CHANNEL3_LANGUAGE: str = "en"
    CHANNEL3_CURRENCY: str = "USD"

    # PayPal Settings
    PAYPAL_ENV: str = "sandbox"
    PAYPAL_BASE_URL: str = "https://api-m.sandbox.paypal.com"
    PAYPAL_CLIENT_ID: str = ""
    PAYPAL_CLIENT_SECRET: str = ""
    PAYPAL_WEBHOOK_ID: str = ""

    # KERNEL Settings
    KERNEL_ENABLED: bool = False
    KERNEL_API_KEY: str = ""

    # Security & Authentication
    SESSION_SECRET: str = "carti-session-secret-change-in-production-32chars"
    SESSION_COOKIE_NAME: str = "carti_session"
    SESSION_EXPIRE_DAYS: int = 7
    SESSION_COOKIE_SECURE: bool = False
    SESSION_COOKIE_SAMESITE: str = "lax"
    SESSION_COOKIE_HTTPONLY: bool = True
    DEMO_USER_ENABLED: bool = True
    DEMO_USER_EMAIL: str = "demo-user@carti.local"
    DEMO_USER_ID: str = "00000000-0000-0000-0000-000000000001"

    # Rate Limiting & Safety
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    RATE_LIMIT_CREATE_REQUESTS_PER_MINUTE: int = 10
    RATE_LIMIT_LOGIN_PER_MINUTE: int = 5
    MAX_REQUEST_BODY_BYTES: int = 1_048_576  # 1MB limit
    LOG_LEVEL: str = "INFO"

    # Allowed CORS Origins
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]
    )

    def is_demo_allowed(self) -> bool:
        """Demo authentication is strictly forbidden in production."""
        if self.APP_ENV.lower() == "production":
            return False
        return self.DEMO_USER_ENABLED

    @model_validator(mode="after")
    def enforce_production_security(self) -> "Settings":
        """Enforce production security hardening."""
        if self.APP_ENV.lower() == "production":
            self.DEMO_USER_ENABLED = False
            self.SESSION_COOKIE_SECURE = True
        return self


settings = Settings()
