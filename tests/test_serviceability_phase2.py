"""
Phase 2 Unit Tests: Nationwide Delivery Serviceability & Indian PIN-Code Validation
"""

import unittest
import os
import sys
import json

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app import models, schemas
from app.utils.geo import is_valid_indian_pincode, clean_pincode
from app.services.serviceability_engine import (
    create_delivery_zone,
    create_shared_drop_point,
    evaluate_serviceability,
    list_active_zones,
    list_active_drop_points,
)
from fastapi import HTTPException


class TestServiceabilityPhase2(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        cls.TestSession = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

    def setUp(self):
        Base.metadata.create_all(bind=self.engine)
        self.db = self.TestSession()

        # Seed sample zones
        self.zone_blr = models.DeliveryZone(
            name="Bangalore Urban Central",
            state="Karnataka",
            district="Bangalore Urban",
            city="Bengaluru",
            serviceable_pincodes=json.dumps(["560001", "560002", "560038", "560068"]),
            min_batch_threshold_kg=20.0,
            max_batch_weight_kg=600.0,
            max_batch_orders=40,
            allows_home_delivery=True,
            allows_drop_point=True,
            is_active=True,
        )
        self.db.add(self.zone_blr)
        self.db.flush()

        # Seed sample drop point
        self.drop_point = models.SharedDropPoint(
            zone_id=self.zone_blr.id,
            name="Indiranagar Metro Hub",
            address_line="Station Rd, Indiranagar",
            city="Bengaluru",
            district="Bangalore Urban",
            state="Karnataka",
            pincode="560038",
            capacity_orders=30,
            is_active=True,
        )
        self.db.add(self.drop_point)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_indian_pincode_regex_validation(self):
        # Valid 6-digit Indian PIN codes (cannot start with 0)
        self.assertTrue(is_valid_indian_pincode("560001"))
        self.assertTrue(is_valid_indian_pincode("110001"))
        self.assertTrue(is_valid_indian_pincode("400001"))
        self.assertTrue(is_valid_indian_pincode("700001"))

        # Invalid PIN codes
        self.assertFalse(is_valid_indian_pincode("012345"))  # Starts with 0
        self.assertFalse(is_valid_indian_pincode("56001"))   # 5 digits
        self.assertFalse(is_valid_indian_pincode("5600001")) # 7 digits
        self.assertFalse(is_valid_indian_pincode("56000A")) # Letters
        self.assertFalse(is_valid_indian_pincode(""))        # Empty
        self.assertFalse(is_valid_indian_pincode(None))      # None

    def test_clean_pincode(self):
        self.assertEqual(clean_pincode(" 560001 "), "560001")
        self.assertEqual(clean_pincode("560 038"), "560038")
        self.assertIsNone(clean_pincode("invalid"))

    def test_serviceability_check_serviceable_pin(self):
        result = evaluate_serviceability(self.db, "560001")
        self.assertTrue(result.serviceable)
        self.assertEqual(result.zone_name, "Bangalore Urban Central")
        self.assertTrue(result.allows_home_delivery)
        self.assertEqual(result.pincode, "560001")

    def test_serviceability_check_with_shared_drop_points(self):
        result = evaluate_serviceability(self.db, "560038")
        self.assertTrue(result.serviceable)
        self.assertTrue(result.allows_drop_point)
        self.assertGreaterEqual(len(result.available_drop_points), 1)
        self.assertEqual(result.available_drop_points[0].name, "Indiranagar Metro Hub")

    def test_serviceability_check_unserviceable_pin(self):
        # Valid Indian PIN, but outside configured zones
        result = evaluate_serviceability(self.db, "110001")
        self.assertFalse(result.serviceable)
        self.assertTrue(len(result.reasons) > 0)
        self.assertTrue(any("not currently covered" in r.lower() or "not covered" in r.lower() for r in result.reasons))

    def test_create_duplicate_zone_name_rejected(self):
        zone_in = schemas.DeliveryZoneCreate(
            name="Bangalore Urban Central",  # duplicate name
            state="Karnataka",
            district="Bangalore Urban",
            serviceable_pincodes=["560099"],
        )
        with self.assertRaises(HTTPException) as ctx:
            create_delivery_zone(self.db, zone_in)
        self.assertEqual(ctx.exception.status_code, 400)

    def test_create_drop_point_invalid_pin_rejected(self):
        with self.assertRaises(Exception):
            schemas.SharedDropPointCreate(
                zone_id=self.zone_blr.id,
                name="Invalid PIN Hub",
                address_line="Some Address",
                city="Bengaluru",
                district="Bangalore",
                state="Karnataka",
                pincode="012345",  # Invalid PIN
            )


if __name__ == "__main__":
    unittest.main()
