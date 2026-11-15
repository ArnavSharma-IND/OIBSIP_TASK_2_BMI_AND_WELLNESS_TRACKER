"""
Input Validation Utilities
Provides robust validation rules for weight, height, usernames, and dates with clear,
user-friendly error messages that keep the application stable and crash-free.
"""

import re
from datetime import datetime
from typing import Tuple


class ValidationError(ValueError):
    """Custom exception raised when input validation fails with a user-facing explanation."""
    pass


def validate_weight(value: any) -> float:
    """
    Validate weight in kilograms.

    Rules:
    - Non-empty
    - Numeric (integer or float)
    - Strictly greater than zero
    - Sensible human bounds: 10.0 kg to 500.0 kg
    """
    if value is None:
        raise ValidationError("Weight field is required.")

    if isinstance(value, str):
        val_str = value.strip()
        if not val_str:
            raise ValidationError("Weight cannot be empty. Please enter your weight in kilograms.")
        try:
            val_float = float(val_str)
        except ValueError:
            raise ValidationError(
                f"'{val_str}' is not a valid number. Please enter weight as a numeric value (e.g. 72.5)."
            )
    elif isinstance(value, (int, float)):
        val_float = float(value)
    else:
        raise ValidationError("Weight must be a numeric value.")

    if val_float <= 0:
        raise ValidationError("Weight must be greater than zero.")

    if val_float < 10.0:
        raise ValidationError("Weight must be at least 10.0 kg for realistic assessment.")

    if val_float > 500.0:
        raise ValidationError("Weight exceeds maximum realistic threshold (500.0 kg).")

    return round(val_float, 2)


def validate_height(value: any) -> float:
    """
    Validate height in metres.

    Rules:
    - Non-empty
    - Numeric (integer or float)
    - Strictly greater than zero
    - Sensible human bounds: 0.50 m to 3.00 m
    - Detects accidental centimetre inputs (e.g. 175 instead of 1.75) and offers guidance.
    """
    if value is None:
        raise ValidationError("Height field is required.")

    if isinstance(value, str):
        val_str = value.strip()
        if not val_str:
            raise ValidationError("Height cannot be empty. Please enter your height in metres.")
        try:
            val_float = float(val_str)
        except ValueError:
            raise ValidationError(
                f"'{val_str}' is not a valid number. Please enter height in metres (e.g. 1.75)."
            )
    elif isinstance(value, (int, float)):
        val_float = float(value)
    else:
        raise ValidationError("Height must be a numeric value.")

    if val_float <= 0:
        raise ValidationError("Height must be greater than zero.")

    # Friendly detection of centimeter input (e.g., 50 <= height <= 300)
    if val_float > 3.0:
        if 50.0 <= val_float <= 300.0:
            suggested = val_float / 100.0
            raise ValidationError(
                f"Height of {val_float:.1f} m is too large. Did you mean {suggested:.2f} m? "
                "Please enter height in metres (e.g., 1.75)."
            )
        raise ValidationError("Height exceeds maximum realistic threshold (3.00 metres).")

    if val_float < 0.50:
        raise ValidationError("Height must be at least 0.50 metres (50 cm).")

    return round(val_float, 3)


def validate_username(name: any) -> str:
    """
    Validate user profile name.

    Rules:
    - Non-empty after whitespace stripping
    - Between 2 and 32 characters
    - Must not contain control characters or dangerous SQL/path characters
    """
    if name is None:
        raise ValidationError("Username cannot be empty.")

    clean_name = str(name).strip()
    if not clean_name:
        raise ValidationError("Username cannot be empty. Please enter a profile name.")

    if len(clean_name) < 2:
        raise ValidationError("Username must be at least 2 characters long.")

    if len(clean_name) > 32:
        raise ValidationError("Username cannot exceed 32 characters.")

    # Allow letters, numbers, spaces, hyphens, periods, underscores
    if not re.match(r"^[\w\s\.-]+$", clean_name, re.UNICODE):
        raise ValidationError(
            "Username can only contain letters, numbers, spaces, hyphens, and underscores."
        )

    return clean_name


def validate_date_string(date_str: str) -> datetime:
    """Validate and parse a date string formatted as YYYY-MM-DD or YYYY-MM-DD HH:MM:SS."""
    if not date_str or not isinstance(date_str, str):
        raise ValidationError("Date string cannot be empty.")

    cleaned = date_str.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            continue

    raise ValidationError(f"Invalid date format '{date_str}'. Expected YYYY-MM-DD.")
