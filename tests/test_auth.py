"""
Unit and Integration Tests for Authentication and Security
Author: Aparna Jha (Testing Engineer)
"""

import unittest
from datetime import timedelta
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
from app.utils.security import hash_password, verify_password, create_access_token, decode_token
from fastapi import HTTPException


class TestAuthAndSecurity(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Create an in-memory SQLite database for test isolation
        cls.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        cls.TestSession = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

    def setUp(self):
        Base.metadata.create_all(bind=self.engine)
        self.db = self.TestSession()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_password_hashing_and_verification(self):
        """Verify bcrypt password hashing generates valid hash and verifies correctly."""
        raw_password = "SecretFarmerPassword123!"
        hashed = hash_password(raw_password)

        self.assertNotEqual(raw_password, hashed)
        self.assertTrue(hashed.startswith("$2b$") or hashed.startswith("$2a$"))
        self.assertTrue(verify_password(raw_password, hashed))
        self.assertFalse(verify_password("WrongPassword!", hashed))

    def test_jwt_token_creation_and_decoding(self):
        """Verify JWT token encoding contains expected payload claims."""
        payload = {"sub": "user-uuid-123", "role": "farmer"}
        token = create_access_token(payload, expires_minutes=30)

        self.assertIsInstance(token, str)
        decoded = decode_token(token)
        self.assertEqual(decoded["sub"], "user-uuid-123")
        self.assertEqual(decoded["role"], "farmer")
        self.assertIn("exp", decoded)

    def test_expired_jwt_token_rejection(self):
        """Verify an expired JWT token raises HTTPException 401."""
        payload = {"sub": "expired-user"}
        # Create token that expired 10 minutes ago
        token = create_access_token(payload, expires_minutes=-10)

        with self.assertRaises(HTTPException) as ctx:
            decode_token(token)
        self.assertEqual(ctx.exception.status_code, 401)

    def test_user_creation_with_farmer_profile(self):
        """Verify creating a user with farmer role and profile persists in DB."""
        user = models.User(
            name="Ramesh Kumar",
            email="ramesh@farm.test",
            phone="9876543210",
            hashed_password=hash_password("Pass1234"),
            role=models.UserRole.farmer,
        )
        self.db.add(user)
        self.db.flush()

        farmer_profile = models.FarmerProfile(
            user_id=user.id,
            farm_or_fpo_name="Kisan FPO",
            pickup_location="Nashik, Maharashtra",
            latitude=20.0,
            longitude=73.78,
        )
        self.db.add(farmer_profile)
        self.db.commit()

        # Query and verify
        saved_user = self.db.query(models.User).filter_by(email="ramesh@farm.test").first()
        self.assertIsNotNone(saved_user)
        self.assertEqual(saved_user.role, models.UserRole.farmer)
        self.assertIsNotNone(saved_user.farmer_profile)
        self.assertEqual(saved_user.farmer_profile.farm_or_fpo_name, "Kisan FPO")

    def test_user_creation_with_buyer_profile(self):
        """Verify creating a user with buyer role and profile persists in DB."""
        user = models.User(
            name="Priya Sharma",
            email="priya@buyer.test",
            hashed_password=hash_password("Pass1234"),
            role=models.UserRole.buyer,
        )
        self.db.add(user)
        self.db.flush()

        buyer_profile = models.BuyerProfile(
            user_id=user.id,
            buyer_type=models.BuyerType.individual,
            default_location="Andheri West, Mumbai",
        )
        self.db.add(buyer_profile)
        self.db.commit()

        saved_buyer = self.db.query(models.User).filter_by(email="priya@buyer.test").first()
        self.assertIsNotNone(saved_buyer)
        self.assertEqual(saved_buyer.buyer_profile.buyer_type, models.BuyerType.individual)


if __name__ == "__main__":
    unittest.main()
