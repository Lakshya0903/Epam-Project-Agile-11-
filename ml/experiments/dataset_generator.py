"""
Generates reproducible, statistically grounded agricultural price time-series
for testing forecasting models and data quality pipelines without external network calls.
"""

import math
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any


COMMODITY_PROFILES = {
    "Tomato": {
        "base_price": 2200.0,
        "volatility": 0.12,
        "seasonal_amplitude": 450.0,
        "mandis": ["Azadpur (Delhi)", "Kolar (Karnataka)", "Vashi (Mumbai)"],
        "spread_pct": 0.08,
    },
    "Onion": {
        "base_price": 2800.0,
        "volatility": 0.15,
        "seasonal_amplitude": 600.0,
        "mandis": ["Lasalgaon (Maharashtra)", "Pimpalgaon (Maharashtra)", "Azadpur (Delhi)"],
        "spread_pct": 0.06,
    },
    "Potato": {
        "base_price": 1400.0,
        "volatility": 0.05,
        "seasonal_amplitude": 200.0,
        "mandis": ["Agra (UP)", "Farrukhabad (UP)", "Kolkata (WB)"],
        "spread_pct": 0.05,
    },
    "Wheat": {
        "base_price": 2450.0,
        "volatility": 0.03,
        "seasonal_amplitude": 120.0,
        "mandis": ["Khanna (Punjab)", "Indore (MP)", "Kota (Rajasthan)"],
        "spread_pct": 0.04,
    },
}


def generate_mandi_time_series(
    days: int = 90,
    end_date_str: str = "2026-11-01",
    seed: int = 42,
) -> List[Dict[str, Any]]:
    """
    Generate synthetic daily records for each commodity across representative mandis.
    Returns sorted list of dictionaries matching backend MandiPriceRecord schema.
    """
    rng = random.Random(seed)
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    start_date = end_date - timedelta(days=days - 1)

    records: List[Dict[str, Any]] = []

    for commodity, profile in COMMODITY_PROFILES.items():
        base = profile["base_price"]
        vol = profile["volatility"]
        amp = profile["seasonal_amplitude"]
        spread = profile["spread_pct"]

        for mandi in profile["mandis"]:
            # Give each mandi a slight fixed geographic basis differential
            mandi_offset = rng.uniform(-0.04, 0.04) * base

            for day_idx in range(days):
                current_date = start_date + timedelta(days=day_idx)
                date_str = current_date.strftime("%Y-%m-%d")

                # Sinusoidal seasonal wave (annual cycle simulated in days)
                seasonal_effect = amp * math.sin(2 * math.pi * day_idx / 60.0)

                # Stochastic random walk step
                noise = rng.gauss(0, base * vol * 0.3)

                modal_price = round(max(200.0, base + mandi_offset + seasonal_effect + noise), 2)
                min_price = round(modal_price * (1.0 - rng.uniform(spread * 0.5, spread * 1.5)), 2)
                max_price = round(modal_price * (1.0 + rng.uniform(spread * 0.5, spread * 1.5)), 2)

                records.append({
                    "date": date_str,
                    "commodity": commodity,
                    "mandi": mandi,
                    "min_price": min_price,
                    "max_price": max_price,
                    "modal_price": modal_price,
                })

    # Sort deterministically by date and commodity
    records.sort(key=lambda r: (r["date"], r["commodity"], r["mandi"]))
    return records


if __name__ == "__main__":
    data = generate_mandi_time_series(days=30, seed=100)
    print("=" * 60)
    print("SYNTHETIC MANDI DATASET GENERATION COMPLETE")
    print(f"Total Daily Observations Generated: {len(data)}")
    print("Sample records (First 3):")
    for r in data[:3]:
        print(f"  {r['date']} | {r['commodity']:<7} | {r['mandi']:<24} | Modal: INR {r['modal_price']}")
    print("=" * 60)
