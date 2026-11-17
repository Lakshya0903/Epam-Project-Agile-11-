"""
Unit and Integration Tests for Produce Catalog and Marketplace
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
from fastapi import HTTPException


class TestProduceCatalog(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        cls.TestSession = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

    def setUp(self):
        Base.metadata.create_all(bind=self.engine)
        self.db = self.TestSession()

        # Create a test farmer
        self.farmer_user = models.User(
            name="Suresh Farmer",
            email="suresh@farmer.test",
            hashed_password=hash_password("Farmer123!"),
            role=models.UserRole.farmer,
        )
        self.db.add(self.farmer_user)
        self.db.flush()

        self.farmer_profile = models.FarmerProfile(
            user_id=self.farmer_user.id,
            farm_or_fpo_name="Green Valley Farm",
            pickup_location="Pune, Maharashtra",
            latitude=18.52,
            longitude=73.85,
        )
        self.db.add(self.farmer_profile)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_add_valid_produce(self):
        """Verify farmer can successfully list produce with valid attributes."""
        produce = models.Produce(
            farmer_id=self.farmer_profile.id,
            product_name="Organic Alphonso Mangoes",
            quantity_available=150.0,
            unit="kg",
            quality_grade="A",
            price_per_unit=120.0,
            available_date=datetime.utcnow(),
            pickup_location="Ratnagiri, Maharashtra",
            status=models.ProduceStatus.available,
        )
        self.db.add(produce)
        self.db.commit()

        queried = self.db.query(models.Produce).filter_by(product_name="Organic Alphonso Mangoes").first()
        self.assertIsNotNone(queried)
        self.assertEqual(queried.quantity_available, 150.0)
        self.assertEqual(queried.price_per_unit, 120.0)
        self.assertEqual(queried.status, models.ProduceStatus.available)

    def test_marketplace_filtering_by_status_and_name(self):
        """Verify marketplace queries only return available items and support search."""
        p1 = models.Produce(
            farmer_id=self.farmer_profile.id,
            product_name="Fresh Tomatoes",
            quantity_available=50.0,
            unit="kg",
            price_per_unit=25.0,
            pickup_location="Pune",
            status=models.ProduceStatus.available,
        )
        p2 = models.Produce(
            farmer_id=self.farmer_profile.id,
            product_name="Red Onions",
            quantity_available=0.0,
            unit="kg",
            price_per_unit=30.0,
            pickup_location="Pune",
            status=models.ProduceStatus.sold_out,
        )
        self.db.add_all([p1, p2])
        self.db.commit()

        # Available only query
        available_items = self.db.query(models.Produce).filter(
            models.Produce.status == models.ProduceStatus.available
        ).all()
        product_names = [p.product_name for p in available_items]
        self.assertIn("Fresh Tomatoes", product_names)
        self.assertNotIn("Red Onions", product_names)

        # Name search query
        search_results = self.db.query(models.Produce).filter(
            models.Produce.status == models.ProduceStatus.available,
            models.Produce.product_name.ilike("%tomato%")
        ).all()
        self.assertEqual(len(search_results), 1)
        self.assertEqual(search_results[0].product_name, "Fresh Tomatoes")

    def test_produce_pydantic_schema_validation(self):
        """Verify Pydantic ProduceCreate schema validates input constraints."""
        valid_payload = schemas.ProduceCreate(
            product_name="Potatoes",
            quantity_available=100.0,
            unit="kg",
            quality_grade="A",
            price_per_unit=20.0,
            pickup_location="Agra, UP"
        )
        self.assertEqual(valid_payload.product_name, "Potatoes")
        self.assertEqual(valid_payload.unit, "kg")


if __name__ == "__main__":
    unittest.main()
