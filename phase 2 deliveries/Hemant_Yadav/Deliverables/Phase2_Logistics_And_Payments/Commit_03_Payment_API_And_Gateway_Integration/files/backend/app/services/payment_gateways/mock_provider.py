"""
Mock Payment Gateway Provider
Primary Maintainer: Anshika Sharma & Aparna Jha
Phase 2: Provides deterministic offline simulation for tests and local development.
"""

import hmac
import hashlib
import uuid
from typing import Dict, Any, Optional

from .base import BasePaymentGateway


class MockPaymentGateway(BasePaymentGateway):
    """
    Deterministic Mock Payment Provider:
    Simulates gateway order creation, HMAC signature verification, and refunds
    without requiring third-party network requests.
    """

    def __init__(self, key_id: str = "mock_key_id", key_secret: str = "mock_secret"):
        self._key_id = key_id
        self._key_secret = key_secret

    @property
    def provider_name(self) -> str:
        return "mock"

    def create_order(
        self,
        amount_inr: float,
        currency: str = "INR",
        receipt: Optional[str] = None,
        notes: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        amount_paise = int(round(amount_inr * 100))
        mock_order_id = f"mock_order_{uuid.uuid4().hex[:12]}"
        return {
            "gateway_order_id": mock_order_id,
            "amount_paise": amount_paise,
            "amount_inr": amount_inr,
            "currency": currency,
            "key_id": self._key_id,
            "status": "created",
            "receipt": receipt or mock_order_id,
            "notes": notes or {},
        }

    def generate_mock_signature(self, gateway_order_id: str, gateway_payment_id: str) -> str:
        """Helper to generate a valid matching HMAC signature for testing."""
        msg = f"{gateway_order_id}|{gateway_payment_id}".encode("utf-8")
        return hmac.new(self._key_secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()

    def verify_payment_signature(
        self,
        gateway_order_id: str,
        gateway_payment_id: str,
        gateway_signature: str,
    ) -> bool:
        expected = self.generate_mock_signature(gateway_order_id, gateway_payment_id)
        # Also allow matching if test supplies "valid_mock_signature" or exact HMAC
        if gateway_signature in (expected, "valid_mock_signature"):
            return True
        return hmac.compare_digest(expected, gateway_signature)

    def verify_webhook_signature(
        self,
        raw_body: bytes,
        signature_header: str,
        secret: Optional[str] = None,
    ) -> bool:
        sec = secret or self._key_secret
        expected = hmac.new(sec.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
        if signature_header in (expected, "valid_mock_webhook_signature"):
            return True
        return hmac.compare_digest(expected, signature_header)

    def create_refund(
        self,
        gateway_payment_id: str,
        amount_inr: Optional[float] = None,
        notes: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        mock_refund_id = f"mock_rfnd_{uuid.uuid4().hex[:12]}"
        return {
            "gateway_refund_id": mock_refund_id,
            "gateway_payment_id": gateway_payment_id,
            "amount_inr": amount_inr,
            "status": "processed",
            "notes": notes or {},
        }

    def get_payment_details(self, gateway_payment_id: str) -> Dict[str, Any]:
        return {
            "gateway_payment_id": gateway_payment_id,
            "status": "captured",
            "method": "upi",
            "currency": "INR",
        }

