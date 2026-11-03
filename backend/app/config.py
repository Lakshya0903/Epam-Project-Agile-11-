"""
Application Configuration Module
Primary Maintainer: Anshika Sharma (Deployment Manager & Backend Dev 1)
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Default to local SQLite database if not overridden by .env or environment variable
    database_url: str = "sqlite:///./farmcart.db"
    secret_key: str = "dev-secret-change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    platform_fee_percent: float = 8.0
    logistics_share_percent: float = 15.0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
