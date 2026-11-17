"""
Phase 2 Unit Tests: Delivery Confirmation Without OTP & 24h Window Initiation
"""

import unittest
import os
import sys
from datetime import datetime, timezone

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app import models
from app.utils.security import hash_password
from app.services.payment_engine import confirm_receiver_receipt
from fastapi import HTTPException


class TestDeliveryConfirmationPhase2(unittest.TestCase):

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
            name="Priya Sharma",
            email="priya@consumer.test",
            hashed_password=hash_password("Pass123!"),
            role=models.UserRole.buyer,
        )
        self.db.add(self.buyer_user)
        self.db.flush()

        self.buyer_profile = models.BuyerProfile(
            user_id=self.buyer_user.id,
            buyer_type=models.BuyerType.individual,
            default_location="Indiranagar, Bengaluru",
        )
        self.db.add(self.buyer_profile)
        self.db.flush()

        # Seed unauthorized user
        self.stranger_user = models.User(
            name="Rando",
            email="rando@test.in",
            hashed_password=hash_password("Pass123!"),
            role=models.UserRole.buyer,
        )
        self.db.add(self.stranger_user)

        # Seed order
        self.order = models.Order(
            buyer_id=self.buyer_profile.id,
            order_type=models.OrderType.individual,
            delivery_location="Indiranagar, Bengaluru",
            pincode="560038",
            delivery_mode="home_delivery",
            delivery_slot="2026-12-01|morning",
            total_amount=1200.0,
            status=models.OrderStatus.out_for_delivery,
        )
        self.db.add(self.order)
        self.db.flush()

        # Seed delivery record
        self.delivery = models.Delivery(
            order_id=self.order.id,
            status=models.DeliveryStatus.in_transit,
            otp="123456",  # Legacy OTP exists, but receiver confirmation does NOT require it
        )
        self.db.add(self.delivery)

        # Seed payment
        self.payment = models.Payment(
            order_id=self.order.id,
            total_amount=1200.0,
            farmer_share=900.0,
            logistics_share=180.0,
            platform_fee=120.0,
            status="pending",
            is_on_hold=True,
        )
        self.db.add(self.payment)
        self.db.commit()

    def tearDown(self):
        self.db.rollback()
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_receiver_confirms_receipt_without_otp(self):
        # Receiver confirms receipt - NO OTP argument provided!
        updated_delivery = confirm_receiver_receipt(
            self.db,
            delivery_id=self.delivery.id,
            actor=self.buyer_user,
            notes="Package received in good condition at doorstep"
        )

        self.assertTrue(updated_delivery.receiver_confirmed)
        self.assertIsNotNone(updated_delivery.confirmed_at)
        self.assertEqual(updated_delivery.status, models.DeliveryStatus.delivered)

        # Order status must progress to delivered
        self.db.refresh(self.order)
        self.assertEqual(self.order.status, models.OrderStatus.delivered)
        self.assertIsNotNone(self.order.delivered_at)

        # Buyer confirmed deadline on payment is recorded to start 24h countdown
        self.db.refresh(self.payment)
        self.assertIsNotNone(self.payment.buyer_confirmation_deadline)

    def test_duplicate_receiver_confirmation_rejected(self):
        # First confirmation
        confirm_receiver_receipt(self.db, delivery_id=self.delivery.id, actor=self.buyer_user)

        # Second attempt should be rejected
        with self.assertRaises(HTTPException) as ctx:
            confirm_receiver_receipt(self.db, delivery_id=self.delivery.id, actor=self.buyer_user)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("already", ctx.exception.detail.lower())

    def test_unauthorized_user_cannot_confirm_delivery(self):
        # Stranger tries to confirm receipt of another buyer's order
        with self.assertRaises(HTTPException) as ctx:
            confirm_receiver_receipt(self.db, delivery_id=self.delivery.id, actor=self.stranger_user)
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn("designated buyer", ctx.exception.detail.lower())


if __name__ == "__main__":
    unittest.main()
