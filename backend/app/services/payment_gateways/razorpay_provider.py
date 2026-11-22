"""
Razorpay Payment Gateway Adapter
Primary Maintainer: Anshika Sharma & Lakshya Raj Malviya
Phase 2: Real-world Indian payment gateway adapter for Razorpay (UPI, Cards, NetBanking)
with HMAC-SHA256 signature verification and sandbox/test mode support.
"""

import hmac
import hashlib
import json
from typing import Dict, Any, Optional
import httpx

from .base import BasePaymentGateway
from ...config import settings


class RazorpayGateway(BasePaymentGateway):
    """
    Razorpay Adapter implementing BasePaymentGateway interface.
    Communicates via Razorpay REST API v1 using httpx with HTTP Basic Auth.
    """

    BASE_URL = "https://api.razorpay.com/v1"

    def __init__(
        self,
        key_id: Optional[str] = None,
        key_secret: Optional[str] = None,
        webhook_secret: Optional[str] = None,
    ):
        self._key_id = key_id or settings.payment_key_id
        self._key_secret = key_secret or settings.payment_key_secret
        self._webhook_secret = webhook_secret or settings.payment_webhook_secret

    @property
    def provider_name(self) -> str:
        return "razorpay"

    def create_order(
        self,
        amount_inr: float,
        currency: str = "INR",
        receipt: Optional[str] = None,
        notes: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        amount_paise = int(round(amount_inr * 100))
        payload = {
            "amount": amount_paise,
            "currency": currency,
            "receipt": receipt or "",
            "notes": notes or {},
            "payment_capture": 1,  # Automatic capture
        }

        # If live credentials are placeholder, return a test sandbox descriptor
        if self._key_id.startswith("rzp_test_placeholder") or "change-me" in self._key_secret:
            return {
                "gateway_order_id": f"order_mock_{receipt or 'rzp'}",
                "amount_paise": amount_paise,
                "amount_inr": amount_inr,
                "currency": currency,
                "key_id": self._key_id,
                "status": "created",
                "notes": notes or {},
            }

        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                f"{self.BASE_URL}/orders",
                auth=(self._key_id, self._key_secret),
                json=payload,
            )
            if resp.status_code >= 400:
                raise RuntimeError(f"Razorpay order creation failed: {resp.text}")
            data = resp.json()

        return {
            "gateway_order_id": data.get("id"),
            "amount_paise": data.get("amount"),
            "amount_inr": amount_inr,
            "currency": data.get("currency", "INR"),
            "key_id": self._key_id,
            "status": data.get("status"),
            "raw_response": data,
        }

    def verify_payment_signature(
        self,
        gateway_order_id: str,
        gateway_payment_id: str,
        gateway_signature: str,
    ) -> bool:
        """
        Razorpay standard signature verification:
        HMAC-SHA256(order_id + "|" + payment_id, secret) == signature
        """
        msg = f"{gateway_order_id}|{gateway_payment_id}".encode("utf-8")
        expected = hmac.new(self._key_secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, gateway_signature)

    def verify_webhook_signature(
        self,
        raw_body: bytes,
        signature_header: str,
        secret: Optional[str] = None,
    ) -> bool:
        """
        Razorpay standard webhook signature verification:
        HMAC-SHA256(raw_body, webhook_secret) == X-Razorpay-Signature
        """
        sec = secret or self._webhook_secret
        expected = hmac.new(sec.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature_header)

    def create_refund(
        self,
        gateway_payment_id: str,
        amount_inr: Optional[float] = None,
        notes: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"notes": notes or {}}
        if amount_inr is not None:
            payload["amount"] = int(round(amount_inr * 100))

        if self._key_id.startswith("rzp_test_placeholder") or "change-me" in self._key_secret:
            return {
                "gateway_refund_id": f"rfnd_mock_{gateway_payment_id}",
                "gateway_payment_id": gateway_payment_id,
                "amount_inr": amount_inr,
                "status": "processed",
            }

        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                f"{self.BASE_URL}/payments/{gateway_payment_id}/refund",
                auth=(self._key_id, self._key_secret),
                json=payload,
            )
            if resp.status_code >= 400:
                raise RuntimeError(f"Razorpay refund failed: {resp.text}")
            data = resp.json()

        return {
            "gateway_refund_id": data.get("id"),
            "gateway_payment_id": gateway_payment_id,
            "amount_paise": data.get("amount"),
            "status": data.get("status"),
        }

    def get_payment_details(self, gateway_payment_id: str) -> Dict[str, Any]:
        if self._key_id.startswith("rzp_test_placeholder"):
            return {
                "gateway_payment_id": gateway_payment_id,
                "status": "captured",
                "method": "upi",
                "currency": "INR",
            }

        with httpx.Client(timeout=10.0) as client:
            resp = client.get(
                f"{self.BASE_URL}/payments/{gateway_payment_id}",
                auth=(self._key_id, self._key_secret),
            )
            if resp.status_code >= 400:
                raise RuntimeError(f"Razorpay fetch payment failed: {resp.text}")
            return resp.json()

