"""
Unit and Integration Tests for Logistics Engine and Partner Selection
Author: Aparna Jha (Testing Engineer)
"""

import unittest
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
from app.utils.geo import haversine_km, estimate_distance_km
from app.services.logistics_engine import _find_best_partner, _requires_cold_chain


class TestLogisticsEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        cls.TestSession = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

    def setUp(self):
        self.db = self.TestSession()

        # Seed partners with different capacities, rates, and cold chain flags
        self.p_bike = models.LogisticsPartner(
            name="Swift Bikes",
            vehicle_type=models.VehicleType.bike,
            capacity_kg=20.0,
            cost_per_km=5.0,
            base_cost=10.0,
            supports_cold_chain=False,
            is_available=True,
            rating=4.5,
        )
        self.p_van = models.LogisticsPartner(
            name="Cold Van Fleet",
            vehicle_type=models.VehicleType.van,
            capacity_kg=300.0,
            cost_per_km=12.0,
            base_cost=80.0,
            supports_cold_chain=True,
            is_available=True,
            rating=4.9,
        )
        self.p_truck = models.LogisticsPartner(
            name="Heavy Trucking",
            vehicle_type=models.VehicleType.truck,
            capacity_kg=2000.0,
            cost_per_km=20.0,
            base_cost=200.0,
            supports_cold_chain=False,
            is_available=True,
            rating=4.2,
        )
        self.db.add_all([self.p_bike, self.p_van, self.p_truck])
        self.db.commit()

    def tearDown(self):
        self.db.rollback()
        self.db.close()

    def test_haversine_and_fallback_distance_calculation(self):
        """Verify Haversine computes expected distance between known coordinates."""
        # Delhi (28.61, 77.20) to Agra (27.17, 78.00) ~ 180 km
        dist = haversine_km(28.61, 77.20, 27.17, 78.00)
        self.assertAlmostEqual(dist, 180.0, delta=20.0)

        # Fallback distance from text labels
        fallback = estimate_distance_km(None, None, None, None, "Delhi", "Agra")
        self.assertGreaterEqual(fallback, 2.0)
        self.assertLessEqual(fallback, 45.0)

    def test_logistics_partner_capacity_filtering(self):
        """Verify partner selection picks the cheapest vehicle with adequate capacity."""
        # For a 15 kg load without cold chain, bike (capacity 20kg, cost 5/km) should be selected
        partner = _find_best_partner(self.db, weight_kg=15.0, distance_km=10.0, need_cold_chain=False)
        self.assertIsNotNone(partner)
        self.assertEqual(partner.vehicle_type, models.VehicleType.bike)

        # For a 150 kg load, bike is too small, van should be selected
        partner_large = _find_best_partner(self.db, weight_kg=150.0, distance_km=10.0, need_cold_chain=False)
        self.assertIsNotNone(partner_large)
        self.assertEqual(partner_large.vehicle_type, models.VehicleType.van)

    def test_cold_chain_requirement_enforcement(self):
        """Verify perishable dairy/poultry products force selection of cold chain vehicle."""
        # Even for a 10 kg load, if cold chain is required, bike is skipped for cold-chain van
        partner = _find_best_partner(self.db, weight_kg=10.0, distance_km=10.0, need_cold_chain=True)
        self.assertIsNotNone(partner)
        self.assertTrue(partner.supports_cold_chain)
        self.assertEqual(partner.name, "Cold Van Fleet")


if __name__ == "__main__":
    unittest.main()
