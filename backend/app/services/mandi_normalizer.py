"""
FarmCart Mandi Normalization & Data Validation Module
Enforces canonical commodity mapping, Indian date standardization,
price boundary validation, and clerical anomaly rejection.
"""

from typing import Dict, Any, Optional, Tuple, List, Set
from datetime import datetime, timezone
import math
import re


# 5 Finalized Supported Commodities and their verified Indian regional aliases
CANONICAL_COMMODITIES: Set[str] = {"Tomato", "Onion", "Potato", "Wheat", "Rice"}

COMMODITY_ALIASES: Dict[str, str] = {
    # Tomato
    "tomato": "Tomato",
    "tomatoes": "Tomato",
    "tamatar": "Tomato",
    "tamatr": "Tomato",
    "hybrid tomato": "Tomato",
    "desi tomato": "Tomato",
    "tomato hybrid": "Tomato",
    "tomato desi": "Tomato",
    "tamatar desi": "Tomato",
    "tamatar hybrid": "Tomato",

    # Onion
    "onion": "Onion",
    "onions": "Onion",
    "pyaz": "Onion",
    "pyaaz": "Onion",
    "kanda": "Onion",
    "kaanda": "Onion",
    "red onion": "Onion",
    "white onion": "Onion",
    "onion red": "Onion",
    "onion white": "Onion",
    "nasik onion": "Onion",
    "nashik onion": "Onion",

    # Potato
    "potato": "Potato",
    "potatoes": "Potato",
    "aloo": "Potato",
    "alu": "Potato",
    "batata": "Potato",
    "bataata": "Potato",
    "jyoti potato": "Potato",
    "potato jyoti": "Potato",
    "chandramukhi": "Potato",
    "desi aloo": "Potato",

    # Wheat
    "wheat": "Wheat",
    "gehun": "Wheat",
    "gehu": "Wheat",
    "gahu": "Wheat",
    "kanak": "Wheat",
    "sharbati": "Wheat",
    "lokwan": "Wheat",
    "wheat lokwan": "Wheat",
    "wheat sharbati": "Wheat",
    "durum": "Wheat",

    # Rice
    "rice": "Rice",
    "chawal": "Rice",
    "chaawal": "Rice",
    "dhan": "Rice",
    "dhaan": "Rice",
    "paddy": "Rice",
    "paddy(dhan)": "Rice",
    "paddy (dhan)": "Rice",
    "common paddy": "Rice",
    "basmati": "Rice",
    "raw rice": "Rice",
    "boiled rice": "Rice",
    "arwa chawal": "Rice",
}


def normalize_commodity(name: Optional[str]) -> Optional[str]:
    """
    Map regional alias or variant to one of the 5 canonical commodities:
    Tomato, Onion, Potato, Wheat, Rice.
    Returns canonical title or None if commodity is unsupported.
    Never silently maps unrelated commodities.
    """
    if not name or not isinstance(name, str):
        return None

    cleaned = name.strip().lower()
    if not cleaned:
        return None

    # Exact or alias match
    if cleaned in COMMODITY_ALIASES:
        return COMMODITY_ALIASES[cleaned]

    # Partial / substring check for common compounds (e.g. "Onion (Nashik)")
    for alias, canonical in COMMODITY_ALIASES.items():
        pattern = r"\b" + re.escape(alias) + r"\b"
        if re.search(pattern, cleaned):
            return canonical

    return None


def parse_arrival_date(raw_date: Any) -> Optional[str]:
    """
    Parse date from various formats returned by APMCs and OGD:
    e.g. '02/11/2026', '2026-11-02', '02-11-2026', '02/11/26'.
    Returns standard ISO 'YYYY-MM-DD' or None if invalid.
    """
    if not raw_date:
        return None

    if isinstance(raw_date, datetime):
        return raw_date.strftime("%Y-%m-%d")

    val = str(raw_date).strip()
    # Try common formats
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d.%m.%Y", "%Y/%m/%d"):
        try:
            dt = datetime.strptime(val, fmt)
            # Guard against impossible future years (e.g. 2099 typo)
            if 2000 <= dt.year <= 2035:
                return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return None


def clean_location_name(name: Optional[str]) -> str:
    """Trim and normalize district or market names into standardized Title Case."""
    if not name:
        return ""
    # Strip non-alphanumeric noise, keep parentheses if present
    cleaned = re.sub(r"\s+", " ", str(name).strip())
    # Return formatted title
    return cleaned.title()


def validate_mandi_record(raw: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Validate and normalize raw mandi dictionary from API or CSV.
    Returns:
      (normalized_dict, None) if valid.
      (None, error_reason) if rejected.
    """
    # 1. State / District / Market
    raw_state = raw.get("state") or raw.get("State") or ""
    raw_district = raw.get("district") or raw.get("District") or ""
    raw_market = raw.get("market") or raw.get("Market") or raw.get("mandi") or raw.get("Mandi") or ""

    state = clean_location_name(raw_state)
    district = clean_location_name(raw_district)
    market = clean_location_name(raw_market)

    if not district or not market:
        return None, "Missing district or market name"

    if not state:
        state = "India"

    # 2. Commodity validation & normalization
    raw_comm = raw.get("commodity") or raw.get("Commodity") or ""
    canonical_comm = normalize_commodity(raw_comm)
    if not canonical_comm:
        return None, f"Unsupported or unrecognized commodity: '{raw_comm}'. Supported: {', '.join(sorted(CANONICAL_COMMODITIES))}"

    # 3. Variety
    raw_variety = raw.get("variety") or raw.get("Variety") or "Common"
    variety = clean_location_name(raw_variety) or "Common"

    # 4. Arrival Date
    raw_date = raw.get("arrival_date") or raw.get("Arrival_Date") or raw.get("date") or raw.get("Date")
    arrival_date = parse_arrival_date(raw_date)
    if not arrival_date:
        return None, f"Unparseable arrival date: '{raw_date}'"

    # 5. Price bounds validation & non-finite rejection
    try:
        raw_min = raw.get("min_price") if raw.get("min_price") is not None else raw.get("Min_Price")
        raw_max = raw.get("max_price") if raw.get("max_price") is not None else raw.get("Max_Price")
        raw_modal = raw.get("modal_price") if raw.get("modal_price") is not None else raw.get("Modal_Price")
        
        if raw_min is None or raw_max is None or raw_modal is None:
            return None, "Missing required price fields (min_price, max_price, modal_price)"

        min_p = float(raw_min)
        max_p = float(raw_max)
        modal_p = float(raw_modal)
    except (ValueError, TypeError):
        return None, "Non-numeric price values provided"

    # Reject non-finite numbers (NaN, Inf, -Inf)
    if math.isnan(min_p) or math.isnan(max_p) or math.isnan(modal_p):
        return None, "Invalid price: NaN (Not-a-Number) values are strictly prohibited"

    if math.isinf(min_p) or math.isinf(max_p) or math.isinf(modal_p):
        return None, "Invalid price: Infinite price values are strictly prohibited"

    if min_p <= 0 or max_p <= 0 or modal_p <= 0:
        return None, f"Prices must be strictly positive (> 0). Given: min={min_p}, max={max_p}, modal={modal_p}"

    if min_p > max_p:
        return None, f"min_price ({min_p}) cannot exceed max_price ({max_p})"

    if not (min_p <= modal_p <= max_p):
        return None, f"modal_price ({modal_p}) must lie between min_price ({min_p}) and max_price ({max_p})"

    # Outlier / clerical typo check (e.g., max_price is 20x higher than min_price)
    if max_p > 15 * min_p:
        return None, f"Implausible price spread (max={max_p} is >15x min={min_p})"

    # 6. Arrivals in tons (optional)
    try:
        raw_arrivals = raw.get("arrivals_ton") if raw.get("arrivals_ton") is not None else (raw.get("Arrivals_Ton") or raw.get("arrivals") or 0.0)
        arrivals_ton = float(raw_arrivals)
        if math.isnan(arrivals_ton) or math.isinf(arrivals_ton):
            arrivals_ton = 0.0
        else:
            arrivals_ton = max(0.0, arrivals_ton)
    except (ValueError, TypeError):
        arrivals_ton = 0.0

    source = str(raw.get("source") or "ogd_api").strip().lower()

    normalized = {
        "state": state,
        "district": district,
        "market": market,
        "commodity": canonical_comm,
        "variety": variety,
        "arrival_date": arrival_date,
        "min_price": round(min_p, 2),
        "max_price": round(max_p, 2),
        "modal_price": round(modal_p, 2),
        "arrivals_ton": round(arrivals_ton, 2),
        "source": source,
    }
    return normalized, None

Displaying mandi_normalizer.py.
