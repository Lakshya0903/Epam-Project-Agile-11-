"""
Payment Gateways Package Initialization & Factory
Primary Maintainer: Anshika Sharma & Lakshya Raj Malviya
"""

from typing import Optional
from .base import BasePaymentGateway
from .mock_provider import MockPaymentGateway
from .razorpay_provider import RazorpayGateway
from ...config import settings


def get_payment_gateway(provider_name: Optional[str] = None) -> BasePaymentGateway:
    """
    Factory function returning the active payment gateway instance.
    Defaults to settings.payment_provider ('mock' or 'razorpay').
    """
    provider = (provider_name or settings.payment_provider).lower().strip()
    if provider == "razorpay":
        return RazorpayGateway()
    return MockPaymentGateway()


__all__ = ["BasePaymentGateway", "MockPaymentGateway", "RazorpayGateway", "get_payment_gateway"]

