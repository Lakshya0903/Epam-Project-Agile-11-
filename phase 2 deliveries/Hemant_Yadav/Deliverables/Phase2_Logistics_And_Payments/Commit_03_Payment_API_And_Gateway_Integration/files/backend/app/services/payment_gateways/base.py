"""
Payment Gateway Abstract Base Interface
Primary Maintainer: Anshika Sharma & Hemant Yadav
Phase 2: Decouples core payment and ledger mechanics from third-party gateway providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BasePaymentGateway(ABC):
    """Abstract payment gateway interface."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Identifier for the gateway provider (e.g. 'mock', 'razorpay')."""
        pass

    @abstractmethod
    def create_order(
        self,
        amount_inr: float,
        currency: str = "INR",
        receipt: Optional[str] = None,
        notes: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Creates an upstream transaction order on the gateway.
        Returns: {
            "gateway_order_id": str,
            "amount_paise": int,
            "currency": str,
            "key_id": Optional[str],
            "raw_response": dict,
        }
        """
        pass

    @abstractmethod
    def verify_payment_signature(
        self,
        gateway_order_id: str,
        gateway_payment_id: str,
        gateway_signature: str,
    ) -> bool:
        """
        Cryptographically verifies payment signature received from client.
        """
        pass

    @abstractmethod
    def verify_webhook_signature(
        self,
        raw_body: bytes,
        signature_header: str,
        secret: Optional[str] = None,
    ) -> bool:
        """
        Validates webhook cryptographic HMAC signature.
        """
        pass

    @abstractmethod
    def create_refund(
        self,
        gateway_payment_id: str,
        amount_inr: Optional[float] = None,
        notes: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Initiates a refund via the payment provider.
        """
        pass

    @abstractmethod
    def get_payment_details(self, gateway_payment_id: str) -> Dict[str, Any]:
        """
        Fetches current payment details from upstream provider.
        """
        pass

