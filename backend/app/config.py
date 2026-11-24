"""
Application Configuration Module
Primary Maintainer: Anshika Sharma (Deployment Manager & Backend Dev 1)
Updated for Phase 2: Nationwide Delivery, Disputes & Payment Gateway Configuration
"""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Default to local SQLite database if not overridden by .env or environment variable
    database_url: str = "sqlite:///./farmcart.db"
    secret_key: str = "dev-secret-change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    platform_fee_percent: float = 8.0
    logistics_share_percent: float = 15.0

    # Phase 2: Payment Gateway & Settlement Configuration
    payment_provider: str = "mock"  # "mock" | "razorpay"
    payment_mode: str = "sandbox"   # "sandbox" | "live"
    payment_key_id: str = "rzp_test_placeholder"
    payment_key_secret: str = "rzp_secret_placeholder"
    payment_webhook_secret: str = "rzp_webhook_secret_placeholder"
    payment_callback_url: str = "http://localhost:8000/payments/callback"
    payment_webhook_url: str = "http://localhost:8000/payments/webhooks/razorpay"
    payment_live_enabled: bool = False

    # Phase 2: Timing, Windows & Upload Buffers
    buyer_confirmation_period_hours: float = 24.0
    dispute_window_hours: float = 24.0
    upload_dir: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads", "disputes")
    max_upload_size_mb: int = 5

    # Phase 2: Batching & Scheduling Configuration Defaults
    default_min_batch_threshold_kg: float = 25.0
    default_max_batch_weight_kg: float = 1000.0
    default_max_batch_orders: int = 50
    default_prep_buffer_hours: float = 4.0
    default_dispatch_buffer_hours: float = 2.0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()

