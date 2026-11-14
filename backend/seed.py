"""
Comprehensive Seed Data for Development & Testing
Primary Maintainer: Swyam Shukla (Database Lead)

Run from backend directory:
    python seed.py

Seeds:
  1. Test Accounts: Farmer, Individual Buyer, Bulk Buyer, Logistics Fleet, Admin
  2. Fleet Vehicles: Truck, Mini Truck, Cold-Chain Van, Local Bike
  3. Produce Listings: Perishables, Staple Crops, Cold-Chain Products
  4. Benchmark Mandi Price History for Market Analytics
"""

from datetime import datetime, timezone
import sys
import os

# Ensure app package resolves
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine, Base
from app import models
from app.utils.security import hash_password

# Ensure all database tables exist
Base.metadata.create_all(bind=engine)
db = SessionLocal()


# ---------- 1. TEST USERS & PROFILES ----------

test_users = [
    {
        "name": "Test Farmer",
        "email": "farmer@test.com",
        "password": "Test123!",
        "role": models.UserRole.farmer,
        "farm_name": "Kisan Demo Farm",
        "location": "Delhi Rural",
    },
    {
        "name": "Test Buyer (Household)",
        "email": "buyer@test.com",
        "password": "Test123!",
        "role": models.UserRole.buyer,
        "buyer_type": models.BuyerType.individual,
        "location": "South Extension, Delhi",
    },
    {
        "name": "Test Bulk Buyer (Supermarket)",
        "email": "bulkbuyer@test.com",
        "password": "Test123!",
        "role": models.UserRole.buyer,
        "buyer_type": models.BuyerType.bulk,
        "location": "Connaught Place, Delhi",
        "business_name": "Delhi Retail Mart",
    },
    {
        "name": "Test Logistics Fleet",
        "email": "logistics@test.com",
        "password": "Test123!",
        "role": models.UserRole.logistics,
    },
    {
        "name": "Platform Administrator",
        "email": "admin@test.com",
        "password": "Test123!",
        "role": models.UserRole.admin,
    },
    {
        "name": "Dispute Reviewer",
        "email": "reviewer@test.com",
        "password": "Test123!",
        "role": models.UserRole.reviewer,
    },
]

for data in test_users:
    user = db.query(models.User).filter(models.User.email == data["email"]).first()
    if not user:
        user = models.User(
            name=data["name"],
            email=data["email"],
            hashed_password=hash_password(data["password"]),
            role=data["role"],
        )
        db.add(user)
        db.flush()

        if data["role"] == models.UserRole.farmer:
            profile = models.FarmerProfile(
                user_id=user.id,
                farm_or_fpo_name=data["farm_name"],
                pickup_location=data["location"],
                latitude=28.70,
                longitude=77.10,
            )
            db.add(profile)
        elif data["role"] == models.UserRole.buyer:
            profile = models.BuyerProfile(
                user_id=user.id,
                buyer_type=data["buyer_type"],
                default_location=data["location"],
                business_name=data.get("business_name"),
                latitude=28.58,
                longitude=77.22,
            )
            db.add(profile)

        print(f"Created user: {data['email']} ({data['role'].value})")
    else:
        print(f"User already exists: {data['email']}")


# ---------- 2. LOGISTICS PARTNERS ----------

partners = [
    dict(
        name="GreenLine Trucking",
        vehicle_type=models.VehicleType.truck,
        capacity_kg=2000,
        cost_per_km=18.0,
        base_cost=150.0,
        supports_cold_chain=True,
        current_location="City Depot North",
        rating=4.8,
    ),
    dict(
        name="QuickHaul Mini Trucks",
        vehicle_type=models.VehicleType.mini_truck,
        capacity_kg=750,
        cost_per_km=12.0,
        base_cost=80.0,
        supports_cold_chain=False,
        current_location="City Depot East",
        rating=4.5,
    ),
    dict(
        name="LocalHop Delivery Van",
        vehicle_type=models.VehicleType.van,
        capacity_kg=300,
        cost_per_km=9.0,
        base_cost=40.0,
        supports_cold_chain=True,
        current_location="City Depot South",
        rating=4.9,
    ),
    dict(
        name="NeighbourGo Bikes",
        vehicle_type=models.VehicleType.bike,
        capacity_kg=25,
        cost_per_km=6.0,
        base_cost=15.0,
        supports_cold_chain=False,
        current_location="City Depot West",
        rating=4.3,
    ),
]

for p in partners:
    exists = db.query(models.LogisticsPartner).filter(models.LogisticsPartner.name == p["name"]).first()
    if not exists:
        db.add(models.LogisticsPartner(**p))
        print(f"Created fleet vehicle: {p['name']} ({p['vehicle_type'].value})")


# ---------- 3. DEMO PRODUCE ITEMS ----------

farmer_profile = db.query(models.FarmerProfile).first()
if farmer_profile:
    demo_produce = [
        dict(
            farmer_id=farmer_profile.id,
            product_name="Fresh Farm Tomatoes",
            quantity_available=200.0,
            unit="kg",
            quality_grade="A",
            price_per_unit=28.0,
            pickup_location="Delhi Rural",
            status=models.ProduceStatus.available,
        ),
        dict(
            farmer_id=farmer_profile.id,
            product_name="Red Onions (Nashik)",
            quantity_available=500.0,
            unit="kg",
            quality_grade="A",
            price_per_unit=24.0,
            pickup_location="Delhi Rural",
            status=models.ProduceStatus.available,
        ),
        dict(
            farmer_id=farmer_profile.id,
            product_name="Agra Potatoes",
            quantity_available=400.0,
            unit="kg",
            quality_grade="A",
            price_per_unit=16.0,
            pickup_location="Delhi Rural",
            status=models.ProduceStatus.available,
        ),
        dict(
            farmer_id=farmer_profile.id,
            product_name="Fresh Organic Milk (Cold Chain)",
            quantity_available=100.0,
            unit="litre",
            quality_grade="A",
            price_per_unit=65.0,
            pickup_location="Delhi Rural",
            status=models.ProduceStatus.available,
        ),
    ]

    for item in demo_produce:
        exists = db.query(models.Produce).filter(models.Produce.product_name == item["product_name"]).first()
        if not exists:
            db.add(models.Produce(**item))
            print(f"Created produce: {item['product_name']}")


# ---------- 4. BENCHMARK MANDI PRICE RECORDS ----------

mandi_records = [
    dict(state="Delhi", district="North", market="Azadpur", commodity="Tomato", arrival_date="2026-11-01", min_price=2400, max_price=3300, modal_price=2850, arrivals_ton=195),
    dict(state="Maharashtra", district="Nashik", market="Lasalgaon", commodity="Onion", arrival_date="2026-11-01", min_price=1850, max_price=2700, modal_price=2300, arrivals_ton=820),
    dict(state="Uttar Pradesh", district="Agra", market="Agra", commodity="Potato", arrival_date="2026-11-01", min_price=1350, max_price=1750, modal_price=1550, arrivals_ton=510),
]

for rec in mandi_records:
    exists = db.query(models.MandiPriceRecord).filter(
        models.MandiPriceRecord.market == rec["market"],
        models.MandiPriceRecord.commodity == rec["commodity"],
        models.MandiPriceRecord.arrival_date == rec["arrival_date"],
    ).first()
    if not exists:
        db.add(models.MandiPriceRecord(**rec))
        print(f"Created mandi benchmark: {rec['commodity']} @ {rec['market']}")



# ---------- 5. PHASE 2: NATIONWIDE DELIVERY ZONES & DROP POINTS ----------

import json

zones_data = [
    dict(
        name="Delhi NCR Central Zone",
        state="Delhi",
        district="Central",
        city="New Delhi",
        serviceable_pincodes=json.dumps(["110001", "110002", "110003", "110004", "110005", "110006", "110049", "110052"]),
        is_active=True,
        min_batch_threshold_kg=25.0,
        max_batch_weight_kg=1000.0,
        max_batch_orders=50,
        preparation_buffer_hours=4.0,
        dispatch_buffer_hours=2.0,
        allows_home_delivery=True,
        allows_drop_point=True,
    ),
    dict(
        name="Mumbai Suburban Zone",
        state="Maharashtra",
        district="Mumbai Suburban",
        city="Mumbai",
        serviceable_pincodes=json.dumps(["400053", "400058", "400069", "400050", "400051"]),
        is_active=True,
        min_batch_threshold_kg=20.0,
        max_batch_weight_kg=800.0,
        max_batch_orders=40,
        preparation_buffer_hours=4.0,
        dispatch_buffer_hours=2.0,
        allows_home_delivery=True,
        allows_drop_point=True,
    ),
    dict(
        name="Nashik Agri Cluster Zone",
        state="Maharashtra",
        district="Nashik",
        city="Nashik",
        serviceable_pincodes=json.dumps(["422001", "422002", "422003", "422301"]),
        is_active=True,
        min_batch_threshold_kg=30.0,
        max_batch_weight_kg=1500.0,
        max_batch_orders=60,
        preparation_buffer_hours=3.0,
        dispatch_buffer_hours=2.0,
        allows_home_delivery=True,
        allows_drop_point=True,
    ),
]

created_zones = {}
for zd in zones_data:
    z = db.query(models.DeliveryZone).filter(models.DeliveryZone.name == zd["name"]).first()
    if not z:
        z = models.DeliveryZone(**zd)
        db.add(z)
        db.flush()
        print(f"Created delivery zone: {z.name}")
    created_zones[z.name] = z

delhi_zone = created_zones.get("Delhi NCR Central Zone")
mumbai_zone = created_zones.get("Mumbai Suburban Zone")

drop_points_data = [
    dict(
        zone_id=delhi_zone.id if delhi_zone else None,
        name="Connaught Place Community Hub",
        address_line="Block B, Inner Circle, Connaught Place",
        locality="Connaught Place",
        city="New Delhi",
        district="Central",
        state="Delhi",
        pincode="110001",
        operating_hours="08:00 - 20:00",
        contact_phone="9811000001",
        capacity_orders=100,
        is_active=True,
        latitude=28.63,
        longitude=77.21,
    ),
    dict(
        zone_id=delhi_zone.id if delhi_zone else None,
        name="South Extension Market Cooperative Hub",
        address_line="Main Market, Part II, South Extension",
        locality="South Extension",
        city="New Delhi",
        district="South",
        state="Delhi",
        pincode="110049",
        operating_hours="09:00 - 21:00",
        contact_phone="9811000049",
        capacity_orders=80,
        is_active=True,
        latitude=28.57,
        longitude=77.22,
    ),
    dict(
        zone_id=mumbai_zone.id if mumbai_zone else None,
        name="Andheri West Station Drop Point",
        address_line="Near Platform 1, Station Road, Andheri West",
        locality="Andheri West",
        city="Mumbai",
        district="Mumbai Suburban",
        state="Maharashtra",
        pincode="400058",
        operating_hours="08:00 - 20:00",
        contact_phone="9820000058",
        capacity_orders=120,
        is_active=True,
        latitude=19.12,
        longitude=72.84,
    ),
]

for dpd in drop_points_data:
    if dpd["zone_id"]:
        dp = db.query(models.SharedDropPoint).filter(models.SharedDropPoint.name == dpd["name"]).first()
        if not dp:
            dp = models.SharedDropPoint(**dpd)
            db.add(dp)
            print(f"Created shared drop point: {dp.name}")


db.commit()
db.close()

print("\n" + "=" * 50)
print("SEED COMPLETED SUCCESSFULLY!")
print("=" * 50)
print("Pre-configured Test Accounts:")
print("  Farmer      : farmer@test.com / Test123!")
print("  Buyer (Ind) : buyer@test.com / Test123!")
print("  Buyer (Bulk): bulkbuyer@test.com / Test123!")
print("  Logistics   : logistics@test.com / Test123!")
print("  Admin       : admin@test.com / Test123!")
print("  Reviewer    : reviewer@test.com / Test123!")
print("=" * 50)
