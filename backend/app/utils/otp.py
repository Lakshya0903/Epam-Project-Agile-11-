"""
OTP Generation Utility
Primary Maintainer: Hemant Yadav (Backend Developer 3)
"""

import secrets


def generate_otp(length: int = 6) -> str:
    """Generate a cryptographically secure random numeric OTP string."""
    return "".join(str(secrets.randbelow(10)) for _ in range(length))
