"""
Agricultural Mandi Data Quality & Hygiene Engine
Author: Mansi Jain (Data Analyst & Testing Engineer)

Audits agricultural pricing feeds for date validity, nomenclature standardization,
outlier detection via Interquartile Range (IQR), and duplicate entry detection.
"""

from typing import List, Dict, Any, Tuple
from datetime import datetime
import re


CANONICAL_COMMODITIES = {
    "tomato": "Tomato",
    "tamatar": "Tomato",
    "onion": "Onion",
    "pyaz": "Onion",
    "kanda": "Onion",
    "potato": "Potato",
    "aloo": "Potato",
    "batata": "Potato",
    "wheat": "Wheat",
    "gehun": "Wheat",
    "rice": "Rice",
    "chawal": "Rice",
    "dhan": "Paddy (Dhan)",
}


def audit_mandi_dataset(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Perform complete data quality audit on a list of mandi records.
    Returns audit statistics, anomalous records, and clean dataset.
    """
    total_records = len(records)
    valid_records = []
    issues = {
        "invalid_date": [],
        "unrecognized_commodity": [],
        "invalid_price_bounds": [],
        "outliers": [],
        "duplicates": [],
    }

    seen_keys = set()

    for idx, r in enumerate(records):
        has_error = False

        # 1. Date format check (YYYY-MM-DD or DD-MM-YYYY)
        raw_date = str(r.get("date", "")).strip()
        parsed_date = None
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
            try:
                parsed_date = datetime.strptime(raw_date, fmt)
                break
            except ValueError:
                pass

        if not parsed_date:
            issues["invalid_date"].append({"index": idx, "record": r, "reason": "Unparseable date format"})
            has_error = True

        # 2. Commodity nomenclature normalization
        raw_comm = str(r.get("commodity", "")).strip().lower()
        if raw_comm not in CANONICAL_COMMODITIES:
            issues["unrecognized_commodity"].append({"index": idx, "record": r, "reason": f"Unknown commodity: {raw_comm}"})
            has_error = True
        else:
            r["normalized_commodity"] = CANONICAL_COMMODITIES[raw_comm]

        # 3. Price boundary validation
        min_p = float(r.get("min_price", 0))
        max_p = float(r.get("max_price", 0))
        modal_p = float(r.get("modal_price", 0))

        if min_p <= 0 or max_p <= 0 or modal_p <= 0 or not (min_p <= modal_p <= max_p):
            issues["invalid_price_bounds"].append({
                "index": idx,
                "record": r,
                "reason": f"Inconsistent prices: min={min_p}, modal={modal_p}, max={max_p}"
            })
            has_error = True

        # 4. Duplicate check (mandi + commodity + date)
        dedup_key = (
            str(r.get("mandi", "")).strip().lower(),
            raw_comm,
            raw_date
        )
        if dedup_key in seen_keys:
            issues["duplicates"].append({"index": idx, "record": r, "reason": "Duplicate key for mandi/commodity/date"})
            has_error = True
        else:
            seen_keys.add(dedup_key)

        if not has_error:
            valid_records.append(r)

    # 5. Outlier Detection via IQR on modal_price per commodity
    commodities = set(r.get("normalized_commodity", "") for r in valid_records if "normalized_commodity" in r)
    for comm in commodities:
        comm_records = [r for r in valid_records if r.get("normalized_commodity") == comm]
        prices = sorted(r["modal_price"] for r in comm_records)
        n = len(prices)
        if n >= 4:
            q1 = prices[n // 4]
            q3 = prices[(3 * n) // 4]
            iqr = q3 - q1
            lower_bound = max(0, q1 - 1.5 * iqr)
            upper_bound = q3 + 1.5 * iqr

            for r in comm_records:
                if r["modal_price"] < lower_bound or r["modal_price"] > upper_bound:
                    issues["outliers"].append({
                        "commodity": comm,
                        "price": r["modal_price"],
                        "bounds": (lower_bound, upper_bound),
                        "mandi": r.get("mandi"),
                    })

    clean_count = len(valid_records)
    error_count = (
        len(issues["invalid_date"])
        + len(issues["unrecognized_commodity"])
        + len(issues["invalid_price_bounds"])
        + len(issues["duplicates"])
    )
    quality_score = round((clean_count / total_records) * 100, 2) if total_records > 0 else 0.0

    return {
        "total_records": total_records,
        "clean_records": clean_count,
        "total_errors": error_count,
        "quality_score_pct": quality_score,
        "issues": issues,
        "clean_dataset": valid_records,
    }


if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from mandi_analysis import SAMPLE_MANDI_DATA

    # Add intentional test anomaly to verify audit detection
    test_data = list(SAMPLE_MANDI_DATA) + [
        {"date": "invalid-date", "commodity": "Tomato", "mandi": "Azadpur", "min_price": 2000, "max_price": 2500, "modal_price": 2200},
        {"date": "2026-11-01", "commodity": "Onion", "mandi": "Lasalgaon", "min_price": 5000, "max_price": 2000, "modal_price": 3000}, # inverted
    ]

    report = audit_mandi_dataset(test_data)
    print("=" * 60)
    print("FARMCART DATA QUALITY AUDIT REPORT")
    print("=" * 60)
    print(f"Total Records Evaluated : {report['total_records']}")
    print(f"Clean Records Passed    : {report['clean_records']}")
    print(f"Data Quality Score      : {report['quality_score_pct']}%")
    print(f"Invalid Date Records    : {len(report['issues']['invalid_date'])}")
    print(f"Invalid Price Bounds    : {len(report['issues']['invalid_price_bounds'])}")
    print(f"Duplicate Keys          : {len(report['issues']['duplicates'])}")
    print(f"Price Outliers Flagged  : {len(report['issues']['outliers'])}")
    print("=" * 60)
