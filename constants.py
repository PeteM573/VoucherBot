from enum import Enum

class StageEvent(Enum):
    """
    Stage completion events for the VoucherBot agent workflow.
    Used to trigger UI updates and state changes at major checkpoints.
    """
    SEARCH_COMPLETE = "search_listings_done"
    VIOLATIONS_COMPLETE = "violations_check_done"
    FILTERING_COMPLETE = "filtering_done"
    BBL_LOOKUP_COMPLETE = "bbl_lookup_done"
    FAVORITES_UPDATED = "favorites_updated"

class RiskLevel(Enum):
    """
    Risk level indicators for building safety assessments.
    Used for consistent risk display across the system.
    """
    SAFE = "✅"
    MODERATE = "⚠️"
    HIGH_RISK = "🚨"
    UNKNOWN = "❓"

class VoucherType(Enum):
    """
    Supported housing voucher types for filtering and search.
    """
    SECTION_8 = "Section 8"
    CITYFHEPS = "CityFHEPS"
    HASA = "HASA"
    HPD = "HPD"
    DSS = "DSS"
    FHEPS = "FHEPS"

class Borough(Enum):
    """
    NYC Borough identifiers for consistent borough handling.
    """
    MANHATTAN = "manhattan"
    BROOKLYN = "brooklyn"
    QUEENS = "queens"
    BRONX = "bronx"
    STATEN_ISLAND = "staten_island"

# UI Constants
DEFAULT_MAX_RENT = 4000
DEFAULT_MIN_BEDROOMS = 1
DEFAULT_MAX_BEDROOMS = 4

# API Constants
CRAIGSLIST_BASE_URL = "https://newyork.craigslist.org"
NYC_OPEN_DATA_VIOLATIONS_URL = "https://data.cityofnewyork.us/resource/wvxf-dwi5.json"
NYC_GEOCLIENT_BASE_URL = "https://api.cityofnewyork.us/geoclient/v1"

# Performance Constants
DEFAULT_CACHE_TTL_SECONDS = 300  # 5 minutes
MAX_RETRY_ATTEMPTS = 3
DEFAULT_REQUEST_TIMEOUT = 30

# Violation Risk Thresholds
VIOLATION_RISK_THRESHOLDS = {
    "safe": 0,        # 0 violations = safe
    "moderate": 20,   # 1-20 violations = moderate risk
    "high": float('inf')  # 20+ violations = high risk
} 