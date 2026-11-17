"""
Phase 2 Unit Tests: Dispute Management Subsystem (24h Window, Evidence Upload, Payment Hold, Reviewer Resolution)
"""

import unittest
import os
import sys
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
from app.services.dispute_engine import (
    submit_dispute,
    attach_dispute_evidence,
    resolve_dispute,
)
from fastapi import HTTPException


class TestDisputesPhase2(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        cls.TestSession = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

    def setUp(self):
        Base.metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.db = self.TestSession()

        # Seed buyer user and profile
        self.buyer_user = models.User(
            name="Rohit Verma",
            email="rohit@buyer.test",
            hashed_password=hash_password("Pass123!"),
            role=models.UserRole.buyer,
        )
        self.db.add(self.buyer_user)
        self.db.flush()

        self.buyer_profile = models.BuyerProfile(
            user_id=self.buyer_user.id,
            buyer_type=models.BuyerType.individual,
            default_location="Whitefield, Bengaluru",
        )
        self.db.add(self.buyer_profile)
        self.db.flush()

        # Seed reviewer user
        self.reviewer_user = models.User(
            name="Operations Reviewer",
            email="reviewer@farmcart.test",
            hashed_password=hash_password("Pass123!"),
            role=models.UserRole.reviewer,
        )
        self.db.add(self.reviewer_user)

        # Seed delivered order delivered 2 hours ago
        self.delivered_time = datetime.now(timezone.utc) - timedelta(hours=2)
        self.order = models.Order(
            buyer_id=self.buyer_profile.id,
            order_type=models.OrderType.individual,
            delivery_location="Whitefield, Bengaluru",
            pincode="560066",
            delivery_mode="home_delivery",
            delivery_slot="2026-12-01|morning",
            total_amount=1500.0,
            status=models.OrderStatus.delivered,
            delivered_at=self.delivered_time,
        )
        self.db.add(self.order)
        self.db.flush()

        # Seed payment
        self.payment = models.Payment(
            order_id=self.order.id,
            total_amount=1500.0,
            farmer_share=1100.0,
            logistics_share=250.0,
            platform_fee=150.0,
            status="pending",
            is_on_hold=False,
        )
        self.db.add(self.payment)
        self.db.commit()

    def tearDown(self):
        self.db.rollback()
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_submit_dispute_within_24h_success(self):
        payload = schemas.DisputeCreate(
            order_id=self.order.id,
            reason=schemas.DisputeReason.damaged_produce,
            description="Produce arrived bruised and completely crushed during transit.",
        )
        dispute = submit_dispute(self.db, buyer=self.buyer_profile, payload=payload)

        self.assertIsNotNone(dispute.id)
        self.assertEqual(dispute.status, models.DisputeStatus.open.value)
        self.assertEqual(dispute.reason, "DAMAGED_PRODUCE")

        # Payment should be placed on hold immediately
        self.db.refresh(self.payment)
        self.assertTrue(self.payment.is_on_hold)
        self.assertEqual(self.payment.status, models.PaymentStatus.on_hold.value)
        self.assertIn("DAMAGED_PRODUCE", self.payment.hold_reason)

    def test_submit_dispute_after_24h_fails(self):
        # Set delivered time to 26 hours ago
        self.order.delivered_at = datetime.now(timezone.utc) - timedelta(hours=26)
        self.db.commit()

        payload = schemas.DisputeCreate(
            order_id=self.order.id,
            reason=schemas.DisputeReason.quality_issue,
            description="Vegetables are not fresh, arrived more than a day ago.",
        )
        with self.assertRaises(HTTPException) as ctx:
            submit_dispute(self.db, buyer=self.buyer_profile, payload=payload)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("expired", ctx.exception.detail.lower())

    def test_submit_dispute_undelivered_order_fails(self):
        # Change status to shipped
        self.order.status = models.OrderStatus.shipped
        self.order.delivered_at = None
        self.db.commit()

        payload = schemas.DisputeCreate(
            order_id=self.order.id,
            reason=schemas.DisputeReason.missing_items,
            description="Items are missing from this pending package.",
        )
        with self.assertRaises(HTTPException) as ctx:
            submit_dispute(self.db, buyer=self.buyer_profile, payload=payload)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("only be filed after delivery", ctx.exception.detail.lower())

    def test_attach_evidence_valid_image(self):
        payload = schemas.DisputeCreate(
            order_id=self.order.id,
            reason=schemas.DisputeReason.damaged_produce,
            description="Produce crushed in carton box, photo attached.",
        )
        dispute = submit_dispute(self.db, buyer=self.buyer_profile, payload=payload)

        fake_jpeg = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"0" * 100
        evidence = attach_dispute_evidence(
            self.db,
            dispute_id=dispute.id,
            actor=self.buyer_user,
            file_bytes=fake_jpeg,
            filename="damaged_tomatoes.jpg",
            mime_type="image/jpeg",
        )
        self.assertIsNotNone(evidence.id)
        self.assertEqual(evidence.mime_type, "image/jpeg")
        self.assertEqual(evidence.file_name, "damaged_tomatoes.jpg")
        self.assertTrue(os.path.exists(evidence.file_path))

    def test_attach_evidence_invalid_mime_rejected(self):
        payload = schemas.DisputeCreate(
            order_id=self.order.id,
            reason=schemas.DisputeReason.wrong_items,
            description="Received wrong items, attached PDF file.",
        )
        dispute = submit_dispute(self.db, buyer=self.buyer_profile, payload=payload)

        with self.assertRaises(HTTPException) as ctx:
            attach_dispute_evidence(
                self.db,
                dispute_id=dispute.id,
                actor=self.buyer_user,
                file_bytes=b"%PDF-1.4...",
                filename="document.pdf",
                mime_type="application/pdf",
            )
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("unsupported file format", ctx.exception.detail.lower())

    def test_reviewer_resolve_refund(self):
        payload = schemas.DisputeCreate(
            order_id=self.order.id,
            reason=schemas.DisputeReason.damaged_produce,
            description="Spoiled greens received upon unboxing.",
        )
        dispute = submit_dispute(self.db, buyer=self.buyer_profile, payload=payload)

        res_payload = schemas.DisputeResolution(
            decision="REFUND",
            notes="Photo evidence verified by reviewer. Approved full customer refund.",
        )
        resolved = resolve_dispute(self.db, dispute_id=dispute.id, reviewer=self.reviewer_user, payload=res_payload)

        self.assertEqual(resolved.status, models.DisputeStatus.resolved_refund.value)
        self.assertEqual(resolved.resolution_decision, "REFUND")

        # Payment state updated
        self.db.refresh(self.payment)
        self.assertFalse(self.payment.is_on_hold)
        self.assertEqual(self.payment.status, models.PaymentStatus.refunded.value)

    def test_reviewer_resolve_release(self):
        payload = schemas.DisputeCreate(
            order_id=self.order.id,
            reason=schemas.DisputeReason.quality_issue,
            description="Tomatoes had minor scratches on peel.",
        )
        dispute = submit_dispute(self.db, buyer=self.buyer_profile, payload=payload)

        res_payload = schemas.DisputeResolution(
            decision="RELEASE",
            notes="Minor cosmetic variation within standard grade B tolerances. Payout released.",
        )
        resolved = resolve_dispute(self.db, dispute_id=dispute.id, reviewer=self.reviewer_user, payload=res_payload)

        self.assertEqual(resolved.status, models.DisputeStatus.resolved_release.value)

        # Payment hold released
        self.db.refresh(self.payment)
        self.assertFalse(self.payment.is_on_hold)

    def test_non_reviewer_cannot_resolve_dispute(self):
        payload = schemas.DisputeCreate(
            order_id=self.order.id,
            reason=schemas.DisputeReason.damaged_produce,
            description="Damaged packaging during rain.",
        )
        dispute = submit_dispute(self.db, buyer=self.buyer_profile, payload=payload)

        res_payload = schemas.DisputeResolution(
            decision="REFUND",
            notes="Unauthorized attempt to resolve",
        )
        with self.assertRaises(HTTPException) as ctx:
            resolve_dispute(self.db, dispute_id=dispute.id, reviewer=self.buyer_user, payload=res_payload)
        self.assertEqual(ctx.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
