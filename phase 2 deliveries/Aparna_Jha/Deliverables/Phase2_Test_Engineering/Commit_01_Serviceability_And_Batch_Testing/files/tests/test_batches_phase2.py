"""
Phase 2 Unit Tests: Automatic Delivery-Batch Engine (Dual Capacity, Thresholds, Cutoffs, Drop Points)
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
from app.services.batch_engine import (
    assign_order_to_batch,
    calculate_schedule_cutoff,
    evaluate_cutoff_batches,
)


class TestBatchesPhase2(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        cls.TestSession = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

    def setUp(self):
        Base.metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.db = self.TestSession()

        # Seed zone
        self.zone = models.DeliveryZone(
            name="Delhi South",
            state="Delhi",
            district="South Delhi",
            city="New Delhi",
            serviceable_pincodes=json.dumps(["110016", "110017"]),
            min_batch_threshold_kg=30.0,  # Configurable threshold: 30kg
            max_batch_weight_kg=100.0, # Max capacity: 100kg
            max_batch_orders=3,       # Max orders: 3
            allows_home_delivery=True,
            allows_drop_point=True,
            is_active=True,
        )
        self.db.add(self.zone)
        self.db.flush()

        # Seed drop point
        self.drop_point = models.SharedDropPoint(
            zone_id=self.zone.id,
            name="Hauz Khas Hub",
            address_line="Market Rd, Hauz Khas",
            city="New Delhi",
            district="South Delhi",
            state="Delhi",
            pincode="110016",
            capacity_orders=20,
            is_active=True,
        )
        self.db.add(self.drop_point)

        # Seed buyer user and profile
        self.buyer_user = models.User(
            name="Test Buyer",
            email="buyer@test.in",
            hashed_password=hash_password("Pass123!"),
            role=models.UserRole.buyer,
        )
        self.db.add(self.buyer_user)
        self.db.flush()

        self.buyer_profile = models.BuyerProfile(
            user_id=self.buyer_user.id,
            buyer_type=models.BuyerType.individual,
            default_location="Hauz Khas, Delhi",
        )
        self.db.add(self.buyer_profile)

        # Seed logistics fleet partner so capacity validation succeeds
        self.fleet_partner = models.LogisticsPartner(
            name="Delhi Express Fleet",
            vehicle_type=models.VehicleType.truck,
            capacity_kg=2000.0,
            cost_per_km=15.0,
            is_available=True,
        )
        self.db.add(self.fleet_partner)
        self.db.commit()

    def tearDown(self):
        self.db.rollback()
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def _create_order(self, weight_kg, mode="home_delivery", drop_point_id=None, slot="2026-12-01|morning"):
        order = models.Order(
            buyer_id=self.buyer_profile.id,
            order_type=models.OrderType.individual,
            delivery_location="Hauz Khas, Delhi",
            pincode="110016",
            zone_id=self.zone.id,
            delivery_mode=mode,
            drop_point_id=drop_point_id,
            delivery_slot=slot,
            total_amount=500.0,
            status=models.OrderStatus.placed,
        )
        self.db.add(order)
        self.db.flush()
        return order

    def test_cutoff_calculation(self):
        cutoff = calculate_schedule_cutoff("2026-12-01|morning", prep_buffer_hours=2.0, dispatch_buffer_minutes=30)
        self.assertIsNotNone(cutoff)
        # Morning slot starts at 09:00 UTC. 09:00 - 2h - 30m = 06:30 UTC
        self.assertEqual(cutoff.hour, 6)
        self.assertEqual(cutoff.minute, 30)

    def test_dual_capacity_weight_limit_creates_new_batch(self):
        # Order 1: 60 kg (fits in 100kg batch)
        o1 = self._create_order(60.0)
        b1 = assign_order_to_batch(self.db, o1, order_weight=60.0)
        self.assertEqual(b1.total_weight_kg, 60.0)
        self.assertEqual(b1.current_order_count, 1)

        # Order 2: 50 kg (60 + 50 = 110 > 100 kg max capacity, so must create a new batch)
        o2 = self._create_order(50.0)
        b2 = assign_order_to_batch(self.db, o2, order_weight=50.0)
        self.assertNotEqual(b1.id, b2.id)
        self.assertEqual(b2.total_weight_kg, 50.0)
        self.assertEqual(b2.current_order_count, 1)

    def test_dual_capacity_order_count_limit_creates_new_batch(self):
        # Max orders per batch is 3
        o1 = self._create_order(5.0)
        b1 = assign_order_to_batch(self.db, o1, order_weight=5.0)

        o2 = self._create_order(5.0)
        b2 = assign_order_to_batch(self.db, o2, order_weight=5.0)
        self.assertEqual(b1.id, b2.id)

        o3 = self._create_order(5.0)
        b3 = assign_order_to_batch(self.db, o3, order_weight=5.0)
        self.assertEqual(b1.id, b3.id)
        self.assertEqual(b1.current_order_count, 3)

        # Order 4: count would be 4 > 3, so must create a new batch
        o4 = self._create_order(5.0)
        b4 = assign_order_to_batch(self.db, o4, order_weight=5.0)
        self.assertNotEqual(b1.id, b4.id)
        self.assertEqual(b4.current_order_count, 1)

    def test_drop_point_isolation_does_not_mix_with_home_delivery(self):
        # Home delivery order
        o_home = self._create_order(10.0, mode="home_delivery")
        b_home = assign_order_to_batch(self.db, o_home, order_weight=10.0)
        self.assertEqual(b_home.delivery_mode, "home_delivery")

        # Drop point order for HUB-DEL-01
        o_dp = self._create_order(10.0, mode="shared_drop_point", drop_point_id=self.drop_point.id)
        b_dp = assign_order_to_batch(self.db, o_dp, order_weight=10.0)
        self.assertEqual(b_dp.delivery_mode, "shared_drop_point")

        # Must not be assigned to the same batch
        self.assertNotEqual(b_home.id, b_dp.id)
        self.assertEqual(b_dp.drop_point_id, self.drop_point.id)

    def test_evaluate_cutoff_batches_below_threshold_flags_review(self):
        # Create a batch with total weight 10 kg (< 30 kg threshold) whose cutoff is in the past
        past_cutoff = datetime.now(timezone.utc) - timedelta(hours=2)
        batch = models.DeliveryBatch(
            zone_id=self.zone.id,
            area_key="DEL-SOUTH",
            delivery_slot="2026-11-01|morning",
            status="open",
            total_weight_kg=10.0,
            current_order_count=1,
            max_weight_kg=100.0,
            max_orders=10,
            min_threshold_kg=30.0,
            cutoff_time=past_cutoff,
        )
        self.db.add(batch)
        self.db.commit()

        updated_batches = evaluate_cutoff_batches(self.db)
        self.db.refresh(batch)
        self.assertGreaterEqual(len(updated_batches), 1)
        self.assertEqual(batch.status, "review_required")


if __name__ == "__main__":
    unittest.main()
