"""Application configuration using Pydantic Settings v2 with production-ready validation and alias support."""

from typing import List, Union, Optional
from pydantic import Field, AliasChoices, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings supporting environment overrides, aliases, and production validation."""

    PROJECT_NAME: str = "Smart Personal Finance API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    ENVIRONMENT: str = "development"  # 'development' | 'production' | 'staging' | 'test'
    DEBUG: bool = True

    # Database URL: defaults to SQLite for local development; supports PostgreSQL in production
    DATABASE_URL: str = "sqlite:///./finance.db"

    # CORS origins: supports comma-separated string or JSON list from CORS_ALLOWED_ORIGINS / ALLOWED_ORIGINS
    ALLOWED_ORIGINS: Union[List[str], str] = Field(
        default=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5500",
            "http://127.0.0.1:5500",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ],
        validation_alias=AliasChoices("ALLOWED_ORIGINS", "CORS_ALLOWED_ORIGINS")
    )

    # JWT Security Configuration (supports SECRET_KEY or JWT_SECRET_KEY)
    SECRET_KEY: str = Field(
        default="dev-secret-key-phase-2-1-smart-finance-backend-32-chars",
        validation_alias=AliasChoices("SECRET_KEY", "JWT_SECRET_KEY")
    )
    ALGORITHM: str = Field(
        default="HS256",
        validation_alias=AliasChoices("ALGORITHM", "JWT_ALGORITHM")
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=1440,
        validation_alias=AliasChoices("ACCESS_TOKEN_EXPIRE_MINUTES", "JWT_EXPIRE_MINUTES")
    )

    # AI Financial Assistant Configuration
    AI_PROVIDER: str = "mock"  # 'gemini' | 'mock'
    AI_API_KEY: Optional[str] = None
    AI_MODEL: str = "gemini-2.5-flash"
    MAX_HISTORY_MESSAGES: int = 10
    MAX_MESSAGE_LENGTH: int = 1000
    AI_TIMEOUT_SECONDS: int = 30

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return [str(i).strip() for i in v if str(i).strip()]
        return []

    @model_validator(mode="after")
    def validate_production_configuration(self) -> "Settings":
        """Validate safety constraints for production environments."""
        env_lower = self.ENVIRONMENT.lower().strip()

        # In production mode, validate strict requirements
        if env_lower == "production":
            # 1. Reject default dev secret key
            insecure_keys = [
                "dev-secret-key-phase-2-1-smart-finance-backend-32-chars",
                "secret",
                "changeme",
                "password",
                "123456"
            ]
            if self.SECRET_KEY in insecure_keys or len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "Production configuration error: SECRET_KEY / JWT_SECRET_KEY must be a cryptographically secure string of at least 32 characters and cannot use default development keys."
                )

            # 2. Prevent unrestricted wildcard CORS when credentials are enabled
            if "*" in self.ALLOWED_ORIGINS:
                raise ValueError(
                    "Production configuration error: ALLOWED_ORIGINS cannot contain '*' wildcard when credential sharing is enabled. Specify explicit frontend domains."
                )

        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        populate_by_name=True
    )


settings = Settings()
