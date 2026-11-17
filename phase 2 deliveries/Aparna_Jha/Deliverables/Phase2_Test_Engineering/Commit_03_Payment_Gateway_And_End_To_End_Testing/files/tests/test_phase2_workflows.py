"""
Phase 2 End-to-End Integration Tests: Complete Workflows
  1. Home Delivery Lifecycle (5-State Canonical Transitions & Payout)
  2. Shared Drop Point Lifecycle (Batch Isolation & Pickup)
  3. Dispute Lifecycle (Hold, Reviewer Resolution & Refund)
  4. Order Cancellation & Inventory Rollback
"""

import unittest
import os
import sys
import json
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
from app.services.order_engine import (
    create_order,
    transition_order_status,
    cancel_order,
)
from app.services.batch_engine import (
    assign_order_to_batch,
    evaluate_cutoff_batches,
)
from app.services.payment_engine import (
    initiate_payment,
    verify_payment,
    confirm_receiver_receipt,
    evaluate_payment_release_eligibility,
    settle_payout,
)
from app.services.payment_gateways import get_payment_gateway
from app.services.dispute_engine import (
    submit_dispute,
    attach_dispute_evidence,
    resolve_dispute,
)


class TestPhase2Workflows(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        cls.TestSession = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

    def setUp(self):
        Base.metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.db = self.TestSession()

        # 1. Delivery Zone & Drop Point
        self.zone = models.DeliveryZone(
            name="Bangalore Central Zone",
            state="Karnataka",
            district="Bangalore Urban",
            city="Bengaluru",
            serviceable_pincodes=json.dumps(["560001", "560038"]),
            min_batch_threshold_kg=100.0,
            max_batch_weight_kg=500.0,
            max_batch_orders=20,
            allows_home_delivery=True,
            allows_drop_point=True,
            is_active=True,
        )
        self.db.add(self.zone)
        self.db.flush()

        self.drop_point = models.SharedDropPoint(
            zone_id=self.zone.id,
            name="MG Road Metro Hub",
            address_line="MG Road Station Concourse",
            city="Bengaluru",
            district="Bangalore Urban",
            state="Karnataka",
            pincode="560001",
            capacity_orders=30,
            is_active=True,
        )
        self.db.add(self.drop_point)

        # 2. Users: Farmer, Buyer, Reviewer
        self.farmer_user = models.User(
            name="Farmer Suresh",
            email="suresh@farm.test",
            hashed_password=hash_password("Pass123!"),
            role=models.UserRole.farmer,
        )
        self.db.add(self.farmer_user)
        self.db.flush()

        self.farmer_profile = models.FarmerProfile(
            user_id=self.farmer_user.id,
            farm_or_fpo_name="Suresh Organic Valley",
            pickup_location="Kolar, Karnataka",
        )
        self.db.add(self.farmer_profile)
        self.db.flush()

        self.buyer_user = models.User(
            name="Anita Desai",
            email="anita@buyer.test",
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

        self.reviewer_user = models.User(
            name="Admin Reviewer",
            email="ops@farmcart.test",
            hashed_password=hash_password("Pass123!"),
            role=models.UserRole.admin,
        )
        self.db.add(self.reviewer_user)

        # 3. Produce Item
        self.produce = models.Produce(
            farmer_id=self.farmer_profile.id,
            product_name="Organic Shimla Apples",
            quantity_available=100.0,
            unit="kg",
            quality_grade="A",
            price_per_unit=120.0,
            pickup_location="Kolar, Karnataka",
            status=models.ProduceStatus.available,
        )
        self.db.add(self.produce)

        # 4. Logistics Fleet
        self.partner = models.LogisticsPartner(
            name="FastTrack Cargo",
            vehicle_type=models.VehicleType.mini_truck,
            capacity_kg=1500.0,
            cost_per_km=12.0,
            is_available=True,
        )
        self.db.add(self.partner)
        self.db.commit()

    def tearDown(self):
        self.db.rollback()
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_workflow_home_delivery_complete_lifecycle(self):
        # Step 1: Create Order with PIN code
        order_in = schemas.OrderCreate(
            order_type=models.OrderType.individual,
            delivery_mode="home_delivery",
            delivery_location="100ft Road, Indiranagar",
            pincode="560038",
            delivery_slot="2026-12-01|morning",
            items=[schemas.OrderItemCreate(produce_id=self.produce.id, quantity=20.0)],
        )
        order = create_order(self.db, buyer=self.buyer_profile, payload=order_in)
        self.assertIn(order.status, (models.OrderStatus.placed, models.OrderStatus.batched))
        self.assertEqual(self.produce.quantity_available, 80.0)  # Inventory reserved

        # Step 2: Payment Initiation & Verification
        init_resp = initiate_payment(self.db, order=order, provider_name="mock")
        payment = self.db.query(models.Payment).filter(models.Payment.id == init_resp.payment_id).first()

        gateway = get_payment_gateway("mock")
        mock_pay_id = "pay_mock_success_1"
        sig = gateway.generate_mock_signature(payment.gateway_order_id, mock_pay_id)
        verify_payment(self.db, payment_id=payment.id, gateway_order_id=payment.gateway_order_id, gateway_payment_id=mock_pay_id, gateway_signature=sig)
        self.assertEqual(payment.status, models.PaymentStatus.paid.value)

        # Step 3: Farmer Confirms Order -> CONFIRMED
        transition_order_status(self.db, order_id=order.id, new_status=models.OrderStatus.confirmed, actor=self.farmer_user)
        self.assertEqual(order.status, models.OrderStatus.confirmed)

        # Step 4: Farmer Marks Processing -> PROCESSING
        transition_order_status(self.db, order_id=order.id, new_status=models.OrderStatus.processing, actor=self.farmer_user)
        self.assertEqual(order.status, models.OrderStatus.processing)

        # Step 5: Verify Order was automatically assigned to batch (20 kg)
        batch = order.batch or self.db.query(models.DeliveryBatch).filter(models.DeliveryBatch.id == order.batch_id).first()
        self.assertIsNotNone(batch)
        self.assertEqual(batch.total_weight_kg, 20.0)

        # Step 6: Dispatch Order -> SHIPPED
        transition_order_status(self.db, order_id=order.id, new_status=models.OrderStatus.shipped, actor=self.reviewer_user)
        self.assertEqual(order.status, models.OrderStatus.shipped)

        # Verify delivery record exists
        delivery = self.db.query(models.Delivery).filter(models.Delivery.order_id == order.id).first()
        self.assertIsNotNone(delivery)

        # Step 7: Receiver Confirms Receipt Without OTP -> DELIVERED
        confirm_receiver_receipt(self.db, delivery_id=delivery.id, actor=self.buyer_user)
        self.db.refresh(order)
        self.db.refresh(payment)
        self.assertEqual(order.status, models.OrderStatus.delivered)
        self.assertTrue(delivery.receiver_confirmed)
        self.assertIsNotNone(payment.buyer_confirmation_deadline)

        # Step 8: Elapsed deadline -> Payout Released & Settled
        payment.buyer_confirmation_deadline = datetime.now(timezone.utc) - timedelta(hours=1)
        self.db.commit()

        self.assertTrue(evaluate_payment_release_eligibility(self.db, payment))
        settled = settle_payout(self.db, payment_id=payment.id)
        self.assertEqual(settled.status, models.PaymentStatus.settled.value)
        self.assertGreater(settled.farmer_share, 0)
        self.assertGreater(settled.platform_fee, 0)

    def test_workflow_shared_drop_point_lifecycle(self):
        # Place order choosing shared drop point
        order_in = schemas.OrderCreate(
            order_type=models.OrderType.individual,
            delivery_mode="shared_drop_point",
            drop_point_id=self.drop_point.id,
            delivery_location="MG Road Metro Concourse",
            pincode="560001",
            delivery_slot="2026-12-01|morning",
            items=[schemas.OrderItemCreate(produce_id=self.produce.id, quantity=10.0)],
        )
        order = create_order(self.db, buyer=self.buyer_profile, payload=order_in)
        self.assertEqual(order.delivery_mode, "shared_drop_point")
        self.assertEqual(order.drop_point_id, self.drop_point.id)

        # Assign to batch: batch must have shared_drop_point mode
        batch = assign_order_to_batch(self.db, order, order_weight=10.0)
        self.assertEqual(batch.delivery_mode, "shared_drop_point")
        self.assertEqual(batch.drop_point_id, self.drop_point.id)

    def test_workflow_dispute_and_refund(self):
        # Create delivered order
        order_in = schemas.OrderCreate(
            order_type=models.OrderType.individual,
            delivery_mode="home_delivery",
            delivery_location="Indiranagar, Bengaluru",
            pincode="560038",
            delivery_slot="2026-12-01|morning",
            items=[schemas.OrderItemCreate(produce_id=self.produce.id, quantity=15.0)],
        )
        order = create_order(self.db, buyer=self.buyer_profile, payload=order_in)

        # Mark delivered 1 hour ago
        now_utc = datetime.now(timezone.utc)
        order.status = models.OrderStatus.delivered
        order.delivered_at = now_utc - timedelta(hours=1)

        # Create payment record
        payment = models.Payment(
            order_id=order.id,
            total_amount=order.total_amount,
            amount_paise=int(round(order.total_amount * 100)),
            platform_fee=144.0,
            logistics_share=180.0,
            farmer_share=1476.0,
            status=models.PaymentStatus.paid.value,
        )
        self.db.add(payment)
        self.db.commit()

        # Buyer files dispute with photo evidence within 24h
        disp_in = schemas.DisputeCreate(
            order_id=order.id,
            reason=schemas.DisputeReason.damaged_produce,
            description="Apples arrived spoiled and damaged in transport.",
        )
        dispute = submit_dispute(self.db, buyer=self.buyer_profile, payload=disp_in)

        # Payment is placed on hold
        self.db.refresh(payment)
        self.assertTrue(payment.is_on_hold)
        self.assertEqual(payment.status, models.PaymentStatus.on_hold.value)

        # Reviewer approves REFUND
        res_in = schemas.DisputeResolution(
            decision="REFUND",
            notes="Full customer refund approved after reviewing photos.",
        )
        resolved = resolve_dispute(self.db, dispute_id=dispute.id, reviewer=self.reviewer_user, payload=res_in)
        self.assertEqual(resolved.status, models.DisputeStatus.resolved_refund.value)

        # Payment refunded
        self.db.refresh(payment)
        self.assertEqual(payment.status, models.PaymentStatus.refunded.value)

    def test_workflow_order_cancellation_and_inventory_rollback(self):
        # Initial inventory is 100 kg
        initial_qty = self.produce.quantity_available
        order_in = schemas.OrderCreate(
            order_type=models.OrderType.individual,
            delivery_mode="home_delivery",
            delivery_location="Indiranagar, Bengaluru",
            pincode="560038",
            delivery_slot="2026-12-01|morning",
            items=[schemas.OrderItemCreate(produce_id=self.produce.id, quantity=30.0)],
        )
        order = create_order(self.db, buyer=self.buyer_profile, payload=order_in)
        self.assertEqual(self.produce.quantity_available, 70.0)

        # Cancel order while in PLACED state
        cancelled_order = cancel_order(self.db, order_id=order.id, actor=self.buyer_user, reason="Buyer changed plan")
        self.assertEqual(cancelled_order.status, models.OrderStatus.cancelled)

        # Inventory must be restored back to initial 100 kg
        self.db.refresh(self.produce)
        self.assertEqual(self.produce.quantity_available, initial_qty)


if __name__ == "__main__":
    unittest.main()
