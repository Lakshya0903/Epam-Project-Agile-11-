"""
Phase 2 Unit Tests: Payment Gateway Abstraction, Signature Verification & Ledger Auditing
"""

import unittest
import os
import sys
import hmac
import hashlib
from datetime import datetime, timezone, timedelta

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app import models, schemas
from app.utils.security import hash_password
from app.services.payment_gateways import get_payment_gateway, MockPaymentGateway
from app.services.payment_engine import (
    initiate_payment,
    verify_payment,
    evaluate_payment_release_eligibility,
    settle_payout,
)
from fastapi import HTTPException


class TestPaymentGatewayPhase2(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        cls.TestSession = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

    def setUp(self):
        Base.metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.db = self.TestSession()

        # Seed buyer
        self.buyer_user = models.User(
            name="Ananya Roy",
            email="ananya@test.in",
            hashed_password=hash_password("Pass123!"),
            role=models.UserRole.buyer,
        )
        self.db.add(self.buyer_user)
        self.db.flush()

        self.buyer_profile = models.BuyerProfile(
            user_id=self.buyer_user.id,
            buyer_type=models.BuyerType.individual,
            default_location="Kolkata, West Bengal",
        )
        self.db.add(self.buyer_profile)
        self.db.flush()

        # Seed farmer
        self.farmer_user = models.User(
            name="Farmer Ramesh",
            email="ramesh@farmer.test",
            hashed_password=hash_password("Pass123!"),
            role=models.UserRole.farmer,
        )
        self.db.add(self.farmer_user)
        self.db.flush()

        self.farmer_profile = models.FarmerProfile(
            user_id=self.farmer_user.id,
            farm_or_fpo_name="Ramesh Organic Produce",
            pickup_location="Hooghly, West Bengal",
        )
        self.db.add(self.farmer_profile)
        self.db.flush()

        # Seed order
        self.order = models.Order(
            buyer_id=self.buyer_profile.id,
            order_type=models.OrderType.individual,
            delivery_location="Salt Lake, Kolkata",
            pincode="700091",
            delivery_mode="home_delivery",
            delivery_slot="2026-12-01|morning",
            total_amount=2500.0,
            status=models.OrderStatus.confirmed,
        )
        self.db.add(self.order)
        self.db.commit()

    def tearDown(self):
        self.db.rollback()
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_gateway_factory_and_mock_provider(self):
        gateway = get_payment_gateway("mock")
        self.assertIsInstance(gateway, MockPaymentGateway)
        self.assertEqual(gateway.provider_name, "mock")

        # Order creation
        resp = gateway.create_order(amount_inr=2500.0, currency="INR", receipt="rec_001")
        self.assertIn("gateway_order_id", resp)
        self.assertEqual(resp["amount_paise"], 250000)

        # Signature verification
        order_id = resp["gateway_order_id"]
        payment_id = "pay_mock_123456"
        valid_sig = gateway.generate_mock_signature(order_id, payment_id)

        self.assertTrue(gateway.verify_payment_signature(order_id, payment_id, valid_sig))
        self.assertFalse(gateway.verify_payment_signature(order_id, payment_id, "invalid_sig"))

    def test_initiate_payment_creates_order_and_ledger_entry(self):
        init_resp = initiate_payment(self.db, order=self.order, provider_name="mock")

        self.assertIsNotNone(init_resp.payment_id)
        self.assertEqual(init_resp.amount_inr, 2500.0)
        self.assertEqual(init_resp.amount_paise, 250000)
        self.assertTrue(init_resp.gateway_order_id.startswith("mock_order_"))

        # Verify ledger audit entry created
        entries = (
            self.db.query(models.PaymentLedgerEntry)
            .filter(models.PaymentLedgerEntry.payment_id == init_resp.payment_id)
            .all()
        )
        statuses = [e.new_status for e in entries]
        self.assertIn(models.PaymentStatus.payment_initiated.value, statuses)

    def test_verify_payment_with_valid_signature_marks_paid(self):
        init_resp = initiate_payment(self.db, order=self.order, provider_name="mock")
        payment = self.db.query(models.Payment).filter(models.Payment.id == init_resp.payment_id).first()

        gateway = get_payment_gateway("mock")
        mock_pay_id = "pay_mock_test_999"
        valid_sig = gateway.generate_mock_signature(payment.gateway_order_id, mock_pay_id)

        verified_payment = verify_payment(
            self.db,
            payment_id=payment.id,
            gateway_order_id=payment.gateway_order_id,
            gateway_payment_id=mock_pay_id,
            gateway_signature=valid_sig,
        )

        self.assertEqual(verified_payment.status, models.PaymentStatus.paid.value)
        self.assertEqual(verified_payment.gateway_payment_id, mock_pay_id)

        # Check ledger entry
        entries = (
            self.db.query(models.PaymentLedgerEntry)
            .filter(models.PaymentLedgerEntry.payment_id == payment.id)
            .all()
        )
        statuses = [e.new_status for e in entries]
        self.assertIn(models.PaymentStatus.paid.value, statuses)

    def test_verify_payment_with_invalid_signature_fails(self):
        init_resp = initiate_payment(self.db, order=self.order, provider_name="mock")
        payment = self.db.query(models.Payment).filter(models.Payment.id == init_resp.payment_id).first()

        with self.assertRaises(HTTPException) as ctx:
            verify_payment(
                self.db,
                payment_id=payment.id,
                gateway_order_id=payment.gateway_order_id,
                gateway_payment_id="pay_tampered",
                gateway_signature="bad_signature_12345",
            )
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("signature verification failed", ctx.exception.detail.lower())

    def test_evaluate_release_eligibility_and_payout_settlement(self):
        # 1. Initiate and pay
        init_resp = initiate_payment(self.db, order=self.order, provider_name="mock")
        payment = self.db.query(models.Payment).filter(models.Payment.id == init_resp.payment_id).first()
        payment.status = models.PaymentStatus.paid.value

        # Order not delivered yet -> Release must be False
        self.assertFalse(evaluate_payment_release_eligibility(self.db, payment))

        # 2. Mark delivered now with 24h deadline in future -> Release must still be False
        now_utc = datetime.now(timezone.utc)
        self.order.status = models.OrderStatus.delivered
        self.order.delivered_at = now_utc
        payment.buyer_confirmation_deadline = now_utc + timedelta(hours=24)
        self.db.commit()

        self.assertFalse(evaluate_payment_release_eligibility(self.db, payment))

        # 3. Simulate deadline elapsed in the past with no disputes -> Release must become True
        payment.buyer_confirmation_deadline = now_utc - timedelta(hours=1)
        self.db.commit()

        self.assertTrue(evaluate_payment_release_eligibility(self.db, payment))

        # 4. Settle payout
        settled_payment = settle_payout(self.db, payment_id=payment.id)
        self.assertEqual(settled_payment.status, models.PaymentStatus.settled.value)
        self.assertIsNotNone(settled_payment.settled_at)


if __name__ == "__main__":
    unittest.main()
