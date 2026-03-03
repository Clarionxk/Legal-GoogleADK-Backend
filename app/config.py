"""
Application configuration using Pydantic Settings.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List, Union


class Settings(BaseSettings):
    """Application settings."""

    # Application
    APP_NAME: str = "LegalLease Live Agent"
    APP_VERSION: str = "2.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    API_V1_PREFIX: str = "/api"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Security
    API_SECRET_KEY: str = "your-secret-key-change-this"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # CORS
    ALLOWED_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8501",
    ]

    @field_validator('ALLOWED_ORIGINS', mode='before')
    @classmethod
    def parse_allowed_origins(cls, v):
        """Parse ALLOWED_ORIGINS from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # Firebase
    # Path to the Firebase service account JSON file
    FIREBASE_SERVICE_ACCOUNT_KEY: str = ""
    # Firebase project ID (can also be inferred from the service account JSON)
    FIREBASE_PROJECT_ID: str = ""

    # Google Gemini / ADK
    GOOGLE_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash-live-001"

    # Contract Settings
    SUPPORTED_COUNTRIES: List[str] = [
        "United States",
        "United Kingdom",
        "Singapore",
        "Australia",
        "Canada",
    ]

    # Subscription tiers
    FREE_TIER_CREDITS: int = 3
    PRO_TIER_CREDITS: int = 50
    ENTERPRISE_TIER_CREDITS: int = -1  # Unlimited

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
