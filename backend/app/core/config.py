import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Scope Guard API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # Database
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/scopeguard"
    
    # JWT Authentication
    SECRET_KEY: str = "scopeguard_super_secret_jwt_key_change_in_production_2026_x7a8b9c0"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # AI Provider Configuration
    AI_PROVIDER: str = "gemini"  # "gemini" or "openai"
    AI_MODEL: str = "gemini-2.5-flash"  # Current Google Gemini production Flash model
    GEMINI_MODEL: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # CORS Allowed Origins (comma-separated string for easy env configuration)
    CORS_ORIGINS: str = (
        "http://localhost:5173,"
        "http://localhost:3000,"
        "http://127.0.0.1:5173,"
        "http://127.0.0.1:3000"
    )

    def get_cors_origins(self) -> list[str]:
        """Returns parsed list of unique CORS origins, stripped of trailing slashes and whitespace."""
        origins = set()
        for item in self.CORS_ORIGINS.split(","):
            cleaned = item.strip().rstrip("/")
            if cleaned:
                origins.add(cleaned)
        return sorted(list(origins))

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

