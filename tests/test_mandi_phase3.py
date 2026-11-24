"""
Phase 3 Automated Test Suite: Mandi Price Intelligence, Caching & Price Guidance
Validates canonical normalization, official OGD client mock ingestion,
TTL cache freshness and stale-data fallbacks, 90-day analytics,
farmer selling-price guidance (Q1-Q3 percentiles), and admin CSV imports.
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
import io
import json
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
for candidate in [
    os.path.abspath(os.path.join(current_dir, "..", "backend")),
    os.path.abspath(os.path.join(os.getcwd(), "backend")),
]:
    if os.path.isdir(candidate) and candidate not in sys.path:
        sys.path.insert(0, candidate)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app import models, schemas
from app.config import settings
from app.utils.security import hash_password, create_access_token
from app.services.mandi_normalizer import (
    CANONICAL_COMMODITIES,
    normalize_commodity,
    parse_arrival_date,
    validate_mandi_record,
)
from app.services.ogd_client import (
    is_ogd_configured,
    fetch_ogd_records,
    OGDError,
    OGDNotConfiguredError,
    OGDTimeoutError,
    OGDResponseError,
)
from app.services.mandi_data_service import (
    get_available_districts,
    get_available_mandis,
    get_cache_metadata,
    sync_mandi_data_on_demand,
    get_mandi_price_history,
    get_mandi_summary_analytics,
    calculate_selling_price_guidance,
    import_mandi_csv_data,
    get_mandi_platform_status,
    is_cache_fresh,
)
from app.routers.analytics import (
    list_districts,
    list_mandis,
    list_mandi_prices,
    market_summary,
    get_selling_price_guidance,
    mandi_platform_status,
)
from fastapi import HTTPException


class TestMandiPhase3(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        cls.TestSession = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

    def setUp(self):
        Base.metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.db = self.TestSession()

        # Ensure OGD API key is None by default in test suite
        self._orig_key = settings.ogd_api_key
        settings.ogd_api_key = None

        # Seed Admin user
        self.admin_user = models.User(
            name="Admin User",
            email="admin_mandi@test.com",
            hashed_password=hash_password("Pass123!"),
            role=models.UserRole.admin,
        )
        # Seed Farmer user
        self.farmer_user = models.User(
            name="Farmer User",
            email="farmer_mandi@test.com",
            hashed_password=hash_password("Pass123!"),
            role=models.UserRole.farmer,
        )
        # Seed Buyer user
        self.buyer_user = models.User(
            name="Buyer User",
            email="buyer_mandi@test.com",
            hashed_password=hash_password("Pass123!"),
            role=models.UserRole.buyer,
        )
        self.db.add_all([self.admin_user, self.farmer_user, self.buyer_user])
        self.db.commit()

        # Seed sample Mandi observations
        self.sample_records = [
            models.MandiPriceRecord(
                state="Delhi", district="North", market="Azadpur", commodity="Tomato",
                variety="Hybrid", arrival_date="2026-11-01", min_price=2000.0, max_price=2600.0,
                modal_price=2300.0, arrivals_ton=150.0, source="seed"
            ),
            models.MandiPriceRecord(
                state="Delhi", district="North", market="Azadpur", commodity="Tomato",
                variety="Hybrid", arrival_date="2026-11-02", min_price=2100.0, max_price=2700.0,
                modal_price=2400.0, arrivals_ton=140.0, source="seed"
            ),
            models.MandiPriceRecord(
                state="Delhi", district="North", market="Azadpur", commodity="Tomato",
                variety="Hybrid", arrival_date="2026-11-03", min_price=2200.0, max_price=2800.0,
                modal_price=2500.0, arrivals_ton=130.0, source="seed"
            ),
            models.MandiPriceRecord(
                state="Delhi", district="North", market="Azadpur", commodity="Tomato",
                variety="Hybrid", arrival_date="2026-11-04", min_price=2300.0, max_price=2900.0,
                modal_price=2600.0, arrivals_ton=120.0, source="seed"
            ),
            models.MandiPriceRecord(
                state="Maharashtra", district="Nashik", market="Lasalgaon", commodity="Onion",
                variety="Red", arrival_date="2026-11-01", min_price=1600.0, max_price=2200.0,
                modal_price=1900.0, arrivals_ton=500.0, source="seed"
            ),
        ]
        self.db.add_all(self.sample_records)
        self.db.commit()

    def tearDown(self):
        settings.ogd_api_key = self._orig_key
        self.db.rollback()
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    # ------------------------------------------------------------
    # 1. COMMODITY NORMALIZATION & ALIAS TESTS
    # ------------------------------------------------------------

    def test_canonical_commodity_normalization(self):
        # 5 Canonical Commodities
        self.assertEqual(normalize_commodity("Tomato"), "Tomato")
        self.assertEqual(normalize_commodity("Onion"), "Onion")
        self.assertEqual(normalize_commodity("Potato"), "Potato")
        self.assertEqual(normalize_commodity("Wheat"), "Wheat")
        self.assertEqual(normalize_commodity("Rice"), "Rice")

        # Regional aliases
        self.assertEqual(normalize_commodity("tamatar"), "Tomato")
        self.assertEqual(normalize_commodity("Tomato Hybrid"), "Tomato")
        self.assertEqual(normalize_commodity("pyaz"), "Onion")
        self.assertEqual(normalize_commodity("kanda"), "Onion")
        self.assertEqual(normalize_commodity("aloo"), "Potato")
        self.assertEqual(normalize_commodity("batata"), "Potato")
        self.assertEqual(normalize_commodity("gehun"), "Wheat")
        self.assertEqual(normalize_commodity("sharbati"), "Wheat")
        self.assertEqual(normalize_commodity("chawal"), "Rice")
        self.assertEqual(normalize_commodity("dhan"), "Rice")
        self.assertEqual(normalize_commodity("paddy"), "Rice")

        # Unrelated commodities must NOT silently map to the 5 categories
        self.assertIsNone(normalize_commodity("Garlic"))
        self.assertIsNone(normalize_commodity("Banana"))
        self.assertIsNone(normalize_commodity("Apple"))
        self.assertIsNone(normalize_commodity("Ginger"))
        self.assertIsNone(normalize_commodity(""))
        self.assertIsNone(normalize_commodity(None))

    def test_parse_arrival_date(self):
        self.assertEqual(parse_arrival_date("2026-11-15"), "2026-11-15")
        self.assertEqual(parse_arrival_date("15/11/2026"), "2026-11-15")
        self.assertEqual(parse_arrival_date("15-11-2026"), "2026-11-15")
        self.assertIsNone(parse_arrival_date("invalid-date"))
        self.assertIsNone(parse_arrival_date(""))
        self.assertIsNone(parse_arrival_date(None))

    def test_validate_mandi_record(self):
        # Valid record
        valid_raw = {
            "state": "Maharashtra",
            "district": "Nashik",
            "market": "Lasalgaon",
            "commodity": "pyaz",
            "variety": "Red",
            "arrival_date": "01/11/2026",
            "min_price": "1800",
            "max_price": "2600",
            "modal_price": "2200",
            "arrivals_ton": "450",
        }
        norm, err = validate_mandi_record(valid_raw)
        self.assertIsNone(err)
        self.assertIsNotNone(norm)
        self.assertEqual(norm["commodity"], "Onion")
        self.assertEqual(norm["arrival_date"], "2026-11-01")
        self.assertEqual(norm["modal_price"], 2200.0)

        # Inverted price test (min > max)
        invalid_prices = dict(valid_raw, min_price="3000", max_price="2000", modal_price="2500")
        norm, err = validate_mandi_record(invalid_prices)
        self.assertIsNone(norm)
        self.assertIn("cannot exceed", err.lower())

        # Modal price out of bounds
        out_of_bounds = dict(valid_raw, min_price="1500", max_price="2500", modal_price="3000")
        norm, err = validate_mandi_record(out_of_bounds)
        self.assertIsNone(norm)
        self.assertIn("must lie between", err.lower())

        # Unsupported commodity
        unsupported = dict(valid_raw, commodity="Mango")
        norm, err = validate_mandi_record(unsupported)
        self.assertIsNone(norm)
        self.assertIn("unsupported", err.lower())

        # Negative price
        negative_p = dict(valid_raw, min_price="-500")
        norm, err = validate_mandi_record(negative_p)
        self.assertIsNone(norm)
        self.assertIn("strictly positive", err.lower())

    # ------------------------------------------------------------
    # 2. OGD CLIENT & ON-DEMAND CACHING TESTS
    # ------------------------------------------------------------

    def test_ogd_client_unconfigured(self):
        settings.ogd_api_key = None
        self.assertFalse(is_ogd_configured())
        with self.assertRaises(OGDNotConfiguredError):
            fetch_ogd_records(district="Nashik", commodity="Onion")

    @patch("urllib.request.urlopen")
    def test_ogd_client_mock_fetch_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_payload = {
            "records": [
                {
                    "state": "Punjab",
                    "district": "Ludhiana",
                    "market": "Khanna",
                    "commodity": "Wheat",
                    "variety": "Sharbati",
                    "arrival_date": "05/11/2026",
                    "min_price": "2300",
                    "max_price": "2600",
                    "modal_price": "2450",
                    "arrivals_ton": "800",
                }
            ]
        }
        mock_response.read.return_value = json.dumps(mock_payload).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        settings.ogd_api_key = "test_key_123"
        records = fetch_ogd_records(district="Ludhiana", commodity="Wheat")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["market"], "Khanna")

    @patch("app.services.mandi_data_service.fetch_ogd_records")
    def test_on_demand_sync_inserts_and_caches(self, mock_fetch):
        mock_fetch.return_value = [
            {
                "state": "Punjab",
                "district": "Ludhiana",
                "market": "Khanna",
                "commodity": "Wheat",
                "variety": "Sharbati",
                "arrival_date": "2026-11-05",
                "min_price": "2200",
                "max_price": "2500",
                "modal_price": "2350",
                "arrivals_ton": "600",
            }
        ]

        # First call triggers sync
        success, msg = sync_mandi_data_on_demand(self.db, district="Ludhiana", market="Khanna", commodity="Wheat")
        self.assertTrue(success)
        self.assertIn("synced_1_records", msg)

        # Verify DB has new record
        wheat_rec = self.db.query(models.MandiPriceRecord).filter(
            models.MandiPriceRecord.market == "Khanna",
            models.MandiPriceRecord.arrival_date == "2026-11-05"
        ).first()
        self.assertIsNotNone(wheat_rec)
        self.assertEqual(wheat_rec.modal_price, 2350.0)
        self.assertEqual(wheat_rec.source, "ogd_api")

        # Second call immediately after should result in cache hit (no extra upstream fetch)
        mock_fetch.reset_mock()
        success2, msg2 = sync_mandi_data_on_demand(self.db, district="Ludhiana", market="Khanna", commodity="Wheat")
        self.assertTrue(success2)
        self.assertEqual(msg2, "cache_hit")
        mock_fetch.assert_not_called()

    @patch("app.services.mandi_data_service.fetch_ogd_records")
    def test_upstream_failure_falls_back_gracefully_to_cache(self, mock_fetch):
        # Simulate network failure on upstream fetch
        mock_fetch.side_effect = OGDTimeoutError("OGD gateway timeout")

        # Call sync
        success, msg = sync_mandi_data_on_demand(self.db, district="North", market="Azadpur", commodity="Tomato")
        self.assertFalse(success)
        self.assertIn("upstream_failed", msg)

        # Existing cached data must still be intact and retrievable
        history = get_mandi_price_history(self.db, district="North", market="Azadpur", commodity="Tomato")
        self.assertGreaterEqual(history["total_count"], 4)
        self.assertTrue(history["is_stale"])

    # ------------------------------------------------------------
    # 3. 90-DAY ANALYTICS & METRICS TESTS
    # ------------------------------------------------------------

    def test_mandi_price_history_unit_conversion(self):
        history = get_mandi_price_history(self.db, district="North", market="Azadpur", commodity="Tomato")
        self.assertEqual(history["total_count"], 4)
        self.assertEqual(history["commodity"], "Tomato")

        # Check Quintal -> Kg conversion (/ 100)
        latest = history["records"][0]
        self.assertEqual(latest.modal_price, 2600.0)
        self.assertEqual(latest.modal_price_kg, 26.0)
        self.assertEqual(latest.min_price_kg, 23.0)
        self.assertEqual(latest.max_price_kg, 29.0)

    def test_summary_analytics_trends_and_moving_average(self):
        summary = get_mandi_summary_analytics(self.db, district="North", market="Azadpur", commodity="Tomato")
        self.assertIsNotNone(summary)
        self.assertEqual(summary["canonical_commodity"], "Tomato")
        self.assertEqual(summary["latest_modal_quintal"], 2600.0)
        self.assertEqual(summary["latest_modal_kg"], 26.0)

        # 4 observations: 2300, 2400, 2500, 2600. Moving avg = (2300+2400+2500+2600)/4 = 2450 / 100 = 24.50 kg
        self.assertEqual(summary["moving_average_kg"], 24.50)

        # Earliest 2300 -> Latest 2600 = +13.04% Upward trend
        self.assertEqual(summary["trend_direction"], "upward")
        self.assertGreater(summary["price_change_pct"], 0)

        # Historical min and max
        self.assertEqual(summary["historical_min_quintal"], 2000.0)
        self.assertEqual(summary["historical_max_quintal"], 2900.0)
        self.assertEqual(summary["historical_min_kg"], 20.0)
        self.assertEqual(summary["historical_max_kg"], 29.0)

        # Series length
        self.assertEqual(len(summary["daily_series"]), 4)

    # ------------------------------------------------------------
    # 4. FARMER SELLING-PRICE GUIDANCE TESTS
    # ------------------------------------------------------------

    def test_selling_price_guidance_q1_q3(self):
        # Tomato has 4 points: 2300, 2400, 2500, 2600
        guidance = calculate_selling_price_guidance(self.db, commodity="Tomato", district="North", market="Azadpur")
        self.assertTrue(guidance["is_sufficient"])
        self.assertEqual(guidance["sample_observations"], 4)
        self.assertIsNotNone(guidance["suggested_min_price_kg"])
        self.assertIsNotNone(guidance["suggested_max_price_kg"])
        self.assertLessEqual(guidance["suggested_min_price_kg"], guidance["suggested_max_price_kg"])
        self.assertIn("Indicative market-based price guidance", guidance["disclaimer"])

    def test_selling_price_guidance_insufficient_history(self):
        # Onion has only 1 observation in setup -> insufficient history (< 3 required)
        guidance = calculate_selling_price_guidance(self.db, commodity="Onion", district="Nashik", market="Lasalgaon")
        self.assertFalse(guidance["is_sufficient"])
        self.assertIn("minimum 3 required", guidance["reason_if_insufficient"].lower())

    def test_selling_price_guidance_unsupported_commodity(self):
        guidance = calculate_selling_price_guidance(self.db, commodity="Strawberry")
        self.assertFalse(guidance["is_sufficient"])
        self.assertIn("not among the supported", guidance["reason_if_insufficient"].lower())

    # ------------------------------------------------------------
    # 5. ADMIN MANUAL CSV IMPORT TESTS
    # ------------------------------------------------------------

    def test_admin_csv_import_success_and_deduplication(self):
        csv_data = """state,district,market,commodity,variety,arrival_date,min_price,max_price,modal_price,arrivals_ton
Haryana,Karnal,Karnal,Rice,Basmati,2026-11-01,3400,4200,3800,500
Haryana,Karnal,Karnal,Rice,Basmati,2026-11-02,3450,4250,3850,480
Haryana,Karnal,Karnal,Rice,Basmati,2026-11-03,3500,4300,3900,450
"""
        result = import_mandi_csv_data(self.db, csv_content=csv_data, filename="karnal_rice.csv")
        self.assertTrue(result["success"])
        self.assertEqual(result["total_rows"], 3)
        self.assertEqual(result["inserted"], 3)
        self.assertEqual(result["rejected"], 0)

        # Second import with identical rows should be skipped (deduplication)
        result2 = import_mandi_csv_data(self.db, csv_content=csv_data, filename="karnal_rice.csv")
        self.assertEqual(result2["inserted"], 0)
        self.assertEqual(result2["skipped"], 3)

    def test_admin_csv_import_with_malformed_rows(self):
        csv_data = """state,district,market,commodity,variety,arrival_date,min_price,max_price,modal_price,arrivals_ton
Delhi,North,Azadpur,Tomato,Hybrid,2026-11-10,2000,2500,2200,100
Delhi,North,Azadpur,InvalidComm,Hybrid,2026-11-10,2000,2500,2200,100
Delhi,North,Azadpur,Tomato,Hybrid,bad-date,2000,2500,2200,100
Delhi,North,Azadpur,Tomato,Hybrid,2026-11-11,2500,2000,2200,100
"""
        result = import_mandi_csv_data(self.db, csv_content=csv_data, filename="mixed.csv")
        self.assertEqual(result["total_rows"], 4)
        self.assertEqual(result["inserted"], 1)
        self.assertEqual(result["rejected"], 3)
        self.assertGreaterEqual(len(result["errors"]), 3)

    # ------------------------------------------------------------
    # 6. ROUTER ENDPOINT DIRECT TESTS
    # ------------------------------------------------------------

    def test_router_locations_districts_and_mandis(self):
        districts = list_districts(db=self.db)
        self.assertIn("North", districts)
        self.assertIn("Nashik", districts)

        mandis = list_mandis(district="North", db=self.db)
        self.assertIn("Azadpur", mandis)

    def test_router_mandi_prices_and_summary(self):
        # Test mandi prices endpoint
        res = list_mandi_prices(district="North", commodity="Tomato", db=self.db)
        self.assertIsInstance(res, schemas.MandiPriceHistoryOut)
        self.assertGreaterEqual(res.total_count, 1)

        # Test summary endpoint
        summary = market_summary(district="North", commodity="Tomato", db=self.db)
        self.assertIsInstance(summary, schemas.MandiSummaryOut)
        self.assertEqual(summary.canonical_commodity, "Tomato")

    def test_router_selling_price_guidance(self):
        guidance = get_selling_price_guidance(commodity="Tomato", district="North", db=self.db)
        self.assertIsInstance(guidance, schemas.SellingPriceGuidanceOut)
        self.assertTrue(guidance.is_sufficient)

    def test_router_status_admin_diagnostic(self):
        status_data = mandi_platform_status(db=self.db, user=self.admin_user)
        self.assertIsInstance(status_data, schemas.MandiStatusOut)
        self.assertIn("Tomato", status_data.commodity_counts)

    # ------------------------------------------------------------
    # 7. REGRESSION & ACCEPTANCE TESTS (DEFECT REMEDIATION)
    # ------------------------------------------------------------

    def test_state_collision_prevention(self):
        """Verify that identical market names in different states do not collide."""
        # Insert City Market in Delhi
        rec1 = models.MandiPriceRecord(
            state="Delhi", district="Central", market="City Market", commodity="Tomato",
            variety="Common", arrival_date="2026-11-01", min_price=2000.0, max_price=2400.0,
            modal_price=2200.0, arrivals_ton=50.0, source="seed"
        )
        # Insert City Market in Karnataka
        rec2 = models.MandiPriceRecord(
            state="Karnataka", district="Bangalore", market="City Market", commodity="Tomato",
            variety="Common", arrival_date="2026-11-01", min_price=3000.0, max_price=3600.0,
            modal_price=3300.0, arrivals_ton=60.0, source="seed"
        )
        self.db.add_all([rec1, rec2])
        self.db.commit()

        # Query Delhi City Market
        delhi_hist = get_mandi_price_history(self.db, state="Delhi", market="City Market", commodity="Tomato")
        self.assertEqual(delhi_hist["total_count"], 1)
        self.assertEqual(delhi_hist["records"][0].modal_price, 2200.0)

        # Query Karnataka City Market
        kar_hist = get_mandi_price_history(self.db, state="Karnataka", market="City Market", commodity="Tomato")
        self.assertEqual(kar_hist["total_count"], 1)
        self.assertEqual(kar_hist["records"][0].modal_price, 3300.0)

    def test_strict_90_day_window_exclusion(self):
        """Verify records older than 90 days are strictly excluded and never returned via fallback."""
        now_utc = datetime.now(timezone.utc)
        old_date = (now_utc.date() - timedelta(days=120)).strftime("%Y-%m-%d")

        old_rec = models.MandiPriceRecord(
            state="Punjab", district="Amritsar", market="Amritsar Mandi", commodity="Wheat",
            variety="Sharbati", arrival_date=old_date, min_price=1800.0, max_price=2200.0,
            modal_price=2000.0, arrivals_ton=200.0, source="seed"
        )
        self.db.add(old_rec)
        self.db.commit()

        # Summary should return None because the only observation is outside 90 days
        summary = get_mandi_summary_analytics(self.db, state="Punjab", market="Amritsar Mandi", commodity="Wheat")
        self.assertIsNone(summary, "Must return None when all records are older than 90 days (no fallback).")

        # History should return 0 records within window
        hist = get_mandi_price_history(self.db, state="Punjab", market="Amritsar Mandi", commodity="Wheat")
        self.assertEqual(hist["total_count"], 0)

    def test_no_cross_mandi_guidance_fallback(self):
        """Ensure guidance for Market A never falls back to Market B or all-India."""
        # Lasalgaon has only 1 record (Onion). Add another mandi with many records
        now_utc = datetime.now(timezone.utc)
        d1 = (now_utc.date() - timedelta(days=5)).strftime("%Y-%m-%d")
        d2 = (now_utc.date() - timedelta(days=4)).strftime("%Y-%m-%d")
        d3 = (now_utc.date() - timedelta(days=3)).strftime("%Y-%m-%d")

        pune_records = [
            models.MandiPriceRecord(state="Maharashtra", district="Pune", market="Pune Mandi", commodity="Onion", variety="Red", arrival_date=d1, min_price=2000, max_price=2400, modal_price=2200, source="seed"),
            models.MandiPriceRecord(state="Maharashtra", district="Pune", market="Pune Mandi", commodity="Onion", variety="Red", arrival_date=d2, min_price=2100, max_price=2500, modal_price=2300, source="seed"),
            models.MandiPriceRecord(state="Maharashtra", district="Pune", market="Pune Mandi", commodity="Onion", variety="Red", arrival_date=d3, min_price=2200, max_price=2600, modal_price=2400, source="seed"),
        ]
        self.db.add_all(pune_records)
        self.db.commit()

        # Lasalgaon has only 1 observation. It must NOT fall back to Pune Mandi
        guidance = calculate_selling_price_guidance(self.db, commodity="Onion", district="Nashik", market="Lasalgaon")
        self.assertFalse(guidance["is_sufficient"])
        self.assertEqual(guidance["sample_observations"], 1)
        self.assertIn("minimum 3 required", guidance["reason_if_insufficient"].lower())

    @patch("app.services.mandi_data_service.fetch_ogd_records")
    def test_first_fetch_failure_timestamp_semantics(self, mock_fetch):
        """Verify failed first fetch records last_attempted_at but keeps last_successful_fetch_at as None."""
        mock_fetch.side_effect = OGDTimeoutError("Gateway down")

        success, msg = sync_mandi_data_on_demand(self.db, state="Gujarat", district="Surat", market="Surat Mandi", commodity="Tomato")
        self.assertFalse(success)

        metadata = get_cache_metadata(self.db, state="Gujarat", district="Surat", market="Surat Mandi", commodity="Tomato")
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata.status, "failed")
        self.assertIsNone(metadata.last_successful_fetch_at)
        self.assertIsNotNone(metadata.last_attempted_at)
        self.assertIsNotNone(metadata.cooldown_until)

    @patch("app.services.mandi_data_service.fetch_ogd_records")
    def test_stale_cache_timestamp_preservation_on_subsequent_failure(self, mock_fetch):
        """Verify failed subsequent fetch preserves existing last_successful_fetch_at."""
        t1 = datetime.now(timezone.utc) - timedelta(hours=8)
        # Seed an existing successful metadata entry
        meta = models.MandiCacheMetadata(
            state="Delhi", district="North", market="Azadpur", commodity="Tomato",
            last_fetched_at=t1, last_successful_fetch_at=t1, last_attempted_at=t1,
            status="success", record_count=4, last_successful_record_count=4, source="ogd_api"
        )
        self.db.add(meta)
        self.db.commit()

        # Simulate subsequent failure
        mock_fetch.side_effect = OGDTimeoutError("Upstream timeout on sync")
        success, msg = sync_mandi_data_on_demand(self.db, state="Delhi", district="North", market="Azadpur", commodity="Tomato")
        self.assertFalse(success)

        self.db.refresh(meta)
        self.assertEqual(meta.status, "failed")
        # last_successful_fetch_at MUST be preserved!
        actual_t = meta.last_successful_fetch_at
        if actual_t and actual_t.tzinfo is None:
            actual_t = actual_t.replace(tzinfo=timezone.utc)
        self.assertEqual(actual_t, t1)
        self.assertIsNotNone(meta.last_attempted_at)

    @patch("app.services.mandi_data_service.fetch_ogd_records")
    def test_retry_cooldown_suppression(self, mock_fetch):
        """Verify failure cooldown suppresses immediate repeated external requests."""
        now_utc = datetime.now(timezone.utc)
        meta = models.MandiCacheMetadata(
            state="All", district="North", market="Azadpur", commodity="Tomato",
            last_attempted_at=now_utc,
            cooldown_until=now_utc + timedelta(minutes=10),
            status="failed", error_message="Service unavailable", source="ogd_api"
        )
        self.db.add(meta)
        self.db.commit()

        success, msg = sync_mandi_data_on_demand(self.db, district="North", market="Azadpur", commodity="Tomato")
        self.assertFalse(success)
        self.assertEqual(msg, "cooldown_active")
        mock_fetch.assert_not_called()

    def test_csv_non_finite_rejection(self):
        """Verify CSV import rejects NaN and Infinite values."""
        csv_nan = """state,district,market,commodity,variety,arrival_date,min_price,max_price,modal_price
Delhi,North,Azadpur,Tomato,Hybrid,2026-11-10,NaN,2500,2200
Delhi,North,Azadpur,Tomato,Hybrid,2026-11-11,2000,inf,2200
"""
        result = import_mandi_csv_data(self.db, csv_content=csv_nan, filename="nan_test.csv")
        self.assertTrue(result["success"])
        self.assertEqual(result["inserted"], 0)
        self.assertEqual(result["rejected"], 2)
        self.assertTrue(any("nan" in err.lower() or "infinite" in err.lower() for err in result["errors"]))

    def test_api_date_and_limit_validation(self):
        """Verify analytics API rejects malformed dates and invalid date order."""
        with self.assertRaises(HTTPException) as ctx:
            list_mandi_prices(district="North", commodity="Tomato", from_date="invalid-date", db=self.db)
        self.assertEqual(ctx.exception.status_code, 400)

        with self.assertRaises(HTTPException) as ctx2:
            list_mandi_prices(district="North", commodity="Tomato", from_date="2026-11-10", to_date="2026-11-01", db=self.db)
        self.assertEqual(ctx2.exception.status_code, 400)

    def test_production_security_hardening(self):
        """Verify production rejects default weak secrets and enforces length >= 32."""
        from app.config import Settings
        # Dev mode allows default secret
        dev_settings = Settings(environment="development", secret_key="dev-secret-change-me")
        self.assertEqual(dev_settings.secret_key, "dev-secret-change-me")

        # Prod mode rejects dev secret
        with self.assertRaises(ValueError) as ctx:
            Settings(environment="production", secret_key="dev-secret-change-me")
        self.assertIn("Production deployment rejected", str(ctx.exception))

        # Prod mode rejects short secret (< 32 chars)
        with self.assertRaises(ValueError) as ctx2:
            Settings(environment="production", secret_key="too-short-secret")
        self.assertIn("at least 32 characters", str(ctx2.exception))

        # Valid prod secret succeeds
        prod_ok = Settings(environment="production", secret_key="a" * 32)
        self.assertEqual(len(prod_ok.secret_key), 32)


if __name__ == "__main__":
    unittest.main()
