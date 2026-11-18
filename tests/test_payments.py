"""
Unit and Integration Tests for Delivery Confirmation, OTP, and Payment Settlement
Author: Aparna Jha (Testing Engineer)
"""

import unittest
from datetime import datetime
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
for candidate in [
    os.path.abspath(os.path.join(current_dir, "..", "backend")),
    os.path.abspath(os.path.join(current_dir, "..", "..", "..", "..", "backend")),
    os.path.abspath(os.path.join(os.getcwd(), "backend")),
]:
    if os.path.isdir(candidate) and candidate not in sys.path:
        sys.path.insert(0, candidate)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app import models
from app.utils.otp import generate_otp
from app.services.payment_engine import confirm_delivery, settle_payment
from fastapi import HTTPException


class TestPaymentAndSettlement(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        cls.TestSession = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

    def setUp(self):
        Base.metadata.create_all(bind=self.engine)
        self.db = self.TestSession()

        # Seed buyer and order
        self.buyer_user = models.User(
            name="Test Buyer",
            email="buyer@paytest.test",
            hashed_password="hash",
            role=models.UserRole.buyer,
        )
        self.db.add(self.buyer_user)
        self.db.flush()

        self.buyer = models.BuyerProfile(
            user_id=self.buyer_user.id,
            buyer_type=models.BuyerType.individual,
            default_location="Delhi",
        )
        self.db.add(self.buyer)
        self.db.flush()

        self.order = models.Order(
            buyer_id=self.buyer.id,
            order_type=models.OrderType.individual,
            delivery_location="Delhi",
            delivery_slot="2026-11-05|morning",
            status=models.OrderStatus.out_for_delivery,
            total_amount=1000.0,
        )
        self.db.add(self.order)
        self.db.flush()

        # Seed delivery with OTP
        self.valid_otp = generate_otp(6)
        self.delivery = models.Delivery(
            order_id=self.order.id,
            delivery_cost=150.0,
            distance_km=15.0,
            otp=self.valid_otp,
            status=models.DeliveryStatus.assigned,
        )
        self.db.add(self.delivery)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_otp_generation_format(self):
        """Verify generated OTP is a 6-digit numeric string."""
        otp = generate_otp(6)
        self.assertEqual(len(otp), 6)
        self.assertTrue(otp.isdigit())

    def test_delivery_confirmation_with_invalid_otp(self):
        """Verify delivery confirmation rejects wrong OTP with HTTP 400."""
        with self.assertRaises(HTTPException) as ctx:
            confirm_delivery(self.db, self.order, otp="000000")
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Invalid OTP", ctx.exception.detail)

    def test_delivery_confirmation_with_valid_otp_and_settlement(self):
        """Verify valid OTP confirms delivery and settles payment atomically."""
        confirmed_delivery = confirm_delivery(self.db, self.order, otp=self.valid_otp)
        self.assertEqual(confirmed_delivery.status, models.DeliveryStatus.delivered)
        self.assertIsNotNone(confirmed_delivery.delivered_at)

        # Check order status updated to paid
        self.db.refresh(self.order)
        self.assertEqual(self.order.status, models.OrderStatus.paid)

        # Check payment record created with expected splits
        payment = self.db.query(models.Payment).filter_by(order_id=self.order.id).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.status, "settled")
        self.assertEqual(payment.total_amount, 1000.0)

        # Default platform fee is 8% of produce (80) + 15% logistics markup (22.5) = 102.5
        # Farmer share = 1000 - 80 = 920.0
        # Logistics share = 150.0
        self.assertEqual(payment.farmer_share, 920.0)
        self.assertEqual(payment.logistics_share, 150.0)
        self.assertAlmostEqual(payment.platform_fee, 102.5, places=1)

    def test_double_confirmation_rejection(self):
        """Verify already delivered order cannot be confirmed twice."""
        confirm_delivery(self.db, self.order, otp=self.valid_otp)
        with self.assertRaises(HTTPException) as ctx:
            confirm_delivery(self.db, self.order, otp=self.valid_otp)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("already confirmed", ctx.exception.detail)


if __name__ == "__main__":
    unittest.main()
