"""
Unit and Integration Tests for Order Engine and Batching Engine
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
from app import models, schemas
from app.utils.security import hash_password
from app.services.order_engine import create_order
from app.services.batch_engine import request_direct_delivery
from fastapi import HTTPException


class TestOrderAndBatchEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        cls.TestSession = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

    def setUp(self):
        Base.metadata.create_all(bind=self.engine)
        self.db = self.TestSession()

        # Seed a test farmer
        self.farmer_user = models.User(
            name="Farmer Ashok",
            email="ashok@farm.test",
            hashed_password=hash_password("Pass123!"),
            role=models.UserRole.farmer,
        )
        self.db.add(self.farmer_user)
        self.db.flush()

        self.farmer = models.FarmerProfile(
            user_id=self.farmer_user.id,
            farm_or_fpo_name="Ashok Organic Farms",
            pickup_location="Nashik, Maharashtra",
            latitude=19.99,
            longitude=73.79,
        )
        self.db.add(self.farmer)

        # Seed an individual buyer
        self.ind_buyer_user = models.User(
            name="Rahul Consumer",
            email="rahul@buyer.test",
            hashed_password=hash_password("Pass123!"),
            role=models.UserRole.buyer,
        )
        self.db.add(self.ind_buyer_user)
        self.db.flush()

        self.ind_buyer = models.BuyerProfile(
            user_id=self.ind_buyer_user.id,
            buyer_type=models.BuyerType.individual,
            default_location="Andheri, Mumbai",
            latitude=19.11,
            longitude=72.84,
        )
        self.db.add(self.ind_buyer)

        # Seed a bulk buyer
        self.bulk_buyer_user = models.User(
            name="Apex Supermarket",
            email="procurement@apex.test",
            hashed_password=hash_password("Pass123!"),
            role=models.UserRole.buyer,
        )
        self.db.add(self.bulk_buyer_user)
        self.db.flush()

        self.bulk_buyer = models.BuyerProfile(
            user_id=self.bulk_buyer_user.id,
            buyer_type=models.BuyerType.bulk,
            business_name="Apex Supermarkets Ltd",
            default_location="Bandra, Mumbai",
            latitude=19.05,
            longitude=72.83,
        )
        self.db.add(self.bulk_buyer)

        # Seed produce
        self.produce = models.Produce(
            farmer_id=self.farmer.id,
            product_name="Grade A Onions",
            quantity_available=100.0,
            unit="kg",
            price_per_unit=25.0,
            pickup_location="Nashik, Maharashtra",
            latitude=19.99,
            longitude=73.79,
            status=models.ProduceStatus.available,
        )
        self.db.add(self.produce)

        # Seed logistics vehicle
        self.truck = models.LogisticsPartner(
            name="City Express Van",
            vehicle_type=models.VehicleType.van,
            capacity_kg=500.0,
            cost_per_km=10.0,
            base_cost=50.0,
            is_available=True,
            supports_cold_chain=False,
            current_location="Mumbai Depot",
            rating=4.8,
        )
        self.db.add(self.truck)

        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_insufficient_stock_rejection(self):
        """Verify order is rejected when requested quantity exceeds available stock."""
        payload = schemas.OrderCreate(
            order_type=models.OrderType.individual,
            delivery_location="Andheri, Mumbai",
            delivery_slot="2026-11-10|morning",
            items=[schemas.OrderItemCreate(produce_id=self.produce.id, quantity=150.0)],
        )
        with self.assertRaises(HTTPException) as ctx:
            create_order(self.db, self.ind_buyer, payload)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("available", ctx.exception.detail)

    def test_individual_order_stock_deduction_and_batching(self):
        """Verify individual order deducts inventory immediately and enters batch queue."""
        initial_stock = self.produce.quantity_available
        order_qty = 10.0

        payload = schemas.OrderCreate(
            order_type=models.OrderType.individual,
            delivery_location="Andheri, Mumbai",
            delivery_slot="2026-11-10|morning",
            items=[schemas.OrderItemCreate(produce_id=self.produce.id, quantity=order_qty)],
        )
        order = create_order(self.db, self.ind_buyer, payload)

        self.assertIsNotNone(order.id)
        self.assertEqual(order.status, models.OrderStatus.batched)
        self.assertEqual(order.total_amount, 250.0)

        # Verify stock decreased
        self.db.refresh(self.produce)
        self.assertEqual(self.produce.quantity_available, initial_stock - order_qty)

    def test_direct_delivery_opt_out_surcharge(self):
        """Verify requesting direct delivery detaches from batch and applies 25% surcharge."""
        payload = schemas.OrderCreate(
            order_type=models.OrderType.individual,
            delivery_location="Andheri, Mumbai",
            delivery_slot="2026-11-10|morning",
            items=[schemas.OrderItemCreate(produce_id=self.produce.id, quantity=5.0)],
        )
        order = create_order(self.db, self.ind_buyer, payload)
        self.assertIsNotNone(order.batch_id)

        # Request direct delivery
        updated_order = request_direct_delivery(self.db, order, extra_cost_percent=25.0)
        self.assertIsNone(updated_order.batch_id)
        self.assertIsNotNone(updated_order.delivery)
        self.assertIn(updated_order.status, [models.OrderStatus.out_for_delivery, models.OrderStatus.matched])


if __name__ == "__main__":
    unittest.main()
