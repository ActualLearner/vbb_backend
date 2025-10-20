"""
Centralized configuration for inventory domain constants.

This module defines all blood-related domain constants, thresholds, and business rules.
Centralizing these values ensures consistent behavior across the application and makes
it easy to adjust clinical parameters (e.g., low-stock threshold, blood expiry days)
without scattered multi-file edits.

All constants can be overridden via environment variables for different
deployment environments.
"""

import os

# ============================================================================
# BLOOD TYPE DEFINITIONS
# ============================================================================

BLOOD_TYPES = [
    ("A+", "A+"),
    ("A-", "A-"),
    ("B+", "B+"),
    ("B-", "B-"),
    ("AB+", "AB+"),
    ("AB-", "AB-"),
    ("O+", "O+"),
    ("O-", "O-"),
]

# ============================================================================
# CLINICAL THRESHOLDS & TIMEOUTS
# ============================================================================

# Low Stock Threshold: triggers a low-stock alert when inventory falls to or
# below this count. Default: 5 units. Adjustable per deployment.
LOW_STOCK_THRESHOLD = int(os.getenv("INVENTORY_LOW_STOCK_THRESHOLD", "5"))

# Standard Blood Expiry Period: Days until a blood unit expires after donation
# Default: 42 days (6 weeks). RFC compliance: Update if clinical guidance changes.
STANDARD_EXPIRY_DAYS = int(os.getenv("INVENTORY_STANDARD_EXPIRY_DAYS", "42"))

# ============================================================================
# FACILITY & LOCATION CONSTRAINTS
# ============================================================================

# Woreda Range: Valid range for Ethiopian woreda (district) codes within a zone
# Min: 1, Max: 20. Enforced in Facility model validation.
WOREDA_MIN = 1
WOREDA_MAX = int(os.getenv("FACILITY_WOREDA_MAX", "20"))

# ============================================================================
# PAGINATION & API LIMITS
# ============================================================================

# Default page size for paginated endpoints
PAGE_SIZE = int(os.getenv("API_PAGE_SIZE", "25"))

# ============================================================================
# BLOOD REQUEST LIFECYCLE DEFAULTS
# ============================================================================

# Used when creating new BloodUnits during the RECEIVE stage
DEFAULT_BLOOD_UNIT_EXPIRY_DAYS = STANDARD_EXPIRY_DAYS  # Alias for clarity


def get_config():
    """
    Returns a dict of all config constants. Useful for passing to services
    or for debugging/logging purposes.
    """
    return {
        "BLOOD_TYPES": BLOOD_TYPES,
        "LOW_STOCK_THRESHOLD": LOW_STOCK_THRESHOLD,
        "STANDARD_EXPIRY_DAYS": STANDARD_EXPIRY_DAYS,
        "WOREDA_MIN": WOREDA_MIN,
        "WOREDA_MAX": WOREDA_MAX,
        "PAGE_SIZE": PAGE_SIZE,
    }
