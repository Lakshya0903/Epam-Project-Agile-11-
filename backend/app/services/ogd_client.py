"""
Open Government Data (OGD) India API Client
Integration service for Government of India AGMARKNET Mandi Price Resource:
UUID: 9ef84268-d588-465a-a308-a864a43d0070
"""

import json
import logging
import time
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, Any, List, Optional

from ..config import settings

logger = logging.getLogger("farmcart.ogd_client")

MAX_RESPONSE_BYTES = 10 * 1024 * 1024  # 10 MB maximum payload read limit
MAX_PAGE_LIMIT = 1000
DEFAULT_MAX_RETRIES = 2


class OGDError(Exception):
    """Base exception for OGD data integration errors."""
    pass


class OGDNotConfiguredError(OGDError):
    """Raised when OGD API key is missing or unconfigured."""
    pass


class OGDTimeoutError(OGDError):
    """Raised when external OGD API request times out."""
    pass


class OGDConnectionError(OGDError):
    """Raised when network or DNS connection to data.gov.in fails."""
    pass


class OGDRateLimitError(OGDError):
    """Raised when OGD API throttles with HTTP 429 Too Many Requests."""
    pass


class OGDResponseError(OGDError):
    """Raised when OGD API returns an HTTP error or unexpected payload format."""
    pass


def is_ogd_configured() -> bool:
    """Return True if an official OGD API key is onboarded in settings."""
    return bool(settings.ogd_api_key and settings.ogd_api_key.strip())


def _build_safe_url_log(base_url: str, params: Dict[str, str]) -> str:
    """Construct sanitized URL for logging that completely redacts credential keys."""
    safe_params = {k: ("***REDACTED***" if k.lower() in ("api-key", "key", "secret", "token") else v) for k, v in params.items()}
    return f"{base_url}?{urllib.parse.urlencode(safe_params)}"


def fetch_ogd_records(
    state: Optional[str] = None,
    district: Optional[str] = None,
    market: Optional[str] = None,
    commodity: Optional[str] = None,
    limit: int = 500,
    offset: int = 0,
    timeout: Optional[float] = None,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> List[Dict[str, Any]]:
    """
    Fetch agricultural mandi records from official data.gov.in AGMARKNET API.
    Builds structured query parameters and filters:
      - filters[state]=...
      - filters[district]=...
      - filters[market]=...
      - filters[commodity]=...
    Handles pagination (offset, limit), bounded response size, rate limits, and transient retries safely.
    Credentials and API keys are strictly redacted from all log messages.
    """
    if not is_ogd_configured():
        raise OGDNotConfiguredError(
            "OGD_API_KEY is not configured in environment settings. Falling back to cached and local records."
        )

    base_url = f"{settings.ogd_base_url.rstrip('/')}/{settings.ogd_resource_uuid}"
    req_timeout = timeout or settings.ogd_request_timeout_seconds
    bounded_limit = max(1, min(limit, MAX_PAGE_LIMIT))

    params: Dict[str, str] = {
        "api-key": settings.ogd_api_key.strip(),
        "format": "json",
        "offset": str(max(0, offset)),
        "limit": str(bounded_limit),
    }

    if state and state.strip() and state.strip().lower() not in ("all", "all states", "india"):
        params["filters[state]"] = state.strip()
    if district and district.strip() and district.strip().lower() not in ("all", "all districts"):
        params["filters[district]"] = district.strip()
    if market and market.strip() and market.strip().lower() not in ("all", "all mandis", "all markets"):
        params["filters[market]"] = market.strip()
    if commodity and commodity.strip() and commodity.strip().lower() != "all":
        params["filters[commodity]"] = commodity.strip()

    query_str = urllib.parse.urlencode(params)
    full_url = f"{base_url}?{query_str}"
    safe_log_url = _build_safe_url_log(base_url, params)

    headers = {
        "User-Agent": "FarmCart-Platform/3.0 (+https://farmcart.in; data-integration)",
        "Accept": "application/json",
    }

    req = urllib.request.Request(full_url, headers=headers, method="GET")

    last_error: Optional[Exception] = None

    for attempt in range(max_retries + 1):
        try:
            logger.info(
                "Fetching official Mandi data from OGD (attempt %d/%d): state=%s, district=%s, market=%s, commodity=%s [Query: %s]",
                attempt + 1, max_retries + 1, state, district, market, commodity, safe_log_url
            )
            with urllib.request.urlopen(req, timeout=req_timeout) as response:
                status_code = response.getcode()
                if status_code != 200:
                    raise OGDResponseError(f"OGD API returned unexpected HTTP status code {status_code}")

                # Enforce bounded response size
                raw_bytes = response.read(MAX_RESPONSE_BYTES + 1)
                if len(raw_bytes) > MAX_RESPONSE_BYTES:
                    raise OGDResponseError(f"OGD API response exceeded maximum bounded size of {MAX_RESPONSE_BYTES} bytes")

                try:
                    payload = json.loads(raw_bytes.decode("utf-8"))
                except json.JSONDecodeError as json_err:
                    raise OGDResponseError("OGD API returned non-JSON or malformed payload") from json_err

                # Validate expected structure
                if not isinstance(payload, dict):
                    raise OGDResponseError("Malformed response payload: expected JSON object")

                # Check for upstream error payload status
                if str(payload.get("status", "")).lower() == "failed":
                    msg = payload.get("message") or "Unknown upstream provider error"
                    raise OGDResponseError(f"OGD API provider reported failure: {msg}")

                records = payload.get("records")
                if records is None:
                    # Check if there is an explicit empty indicator or total 0
                    if payload.get("total") == 0 or payload.get("count") == 0:
                        records = []
                    else:
                        raise OGDResponseError("OGD response missing 'records' key in payload")

                if not isinstance(records, list):
                    raise OGDResponseError(f"OGD response 'records' field must be a list, received {type(records).__name__}")

                logger.info(
                    "Successfully fetched %d records from OGD resource %s (offset=%d, limit=%d)",
                    len(records), settings.ogd_resource_uuid, offset, bounded_limit
                )
                return records

        except urllib.error.HTTPError as http_err:
            last_error = http_err
            if http_err.code == 429:
                logger.warning("OGD API Rate Limit exceeded (HTTP 429)")
                raise OGDRateLimitError("OGD API rate limit reached (HTTP 429). Retry throttled.") from http_err
            if 500 <= http_err.code < 600 and attempt < max_retries:
                backoff = min(1.0 * (2 ** attempt), 4.0)
                logger.warning("OGD API HTTP %d transient error on attempt %d; retrying in %.1fs", http_err.code, attempt + 1, backoff)
                time.sleep(backoff)
                continue
            logger.warning("OGD API HTTP Error %d: %s", http_err.code, http_err.reason)
            raise OGDResponseError(f"OGD API HTTP Error {http_err.code}: {http_err.reason}") from http_err

        except (urllib.error.URLError, TimeoutError) as net_err:
            last_error = net_err
            reason_str = str(net_err).lower()
            is_timeout = "timed out" in reason_str or isinstance(net_err, TimeoutError)

            if attempt < max_retries:
                backoff = min(1.0 * (2 ** attempt), 4.0)
                logger.warning("OGD network/timeout error on attempt %d; retrying in %.1fs: %s", attempt + 1, backoff, net_err)
                time.sleep(backoff)
                continue

            if is_timeout:
                logger.warning("OGD API request timed out after %.1fs", req_timeout)
                raise OGDTimeoutError(f"OGD API request timed out after {req_timeout}s") from net_err

            logger.warning("Network connection to data.gov.in failed: %s", net_err)
            raise OGDConnectionError(f"Connection to official data.gov.in failed: {net_err}") from net_err

        except OGDError:
            raise

        except Exception as exc:
            logger.error("Unexpected error querying OGD API: %s", exc)
            raise OGDError(f"Unexpected OGD API error: {exc}") from exc

    if isinstance(last_error, Exception):
        raise OGDError(f"Failed to fetch OGD records after {max_retries + 1} attempts: {last_error}") from last_error
    return []
