"""
Unit Tests for User Input Validation
Tests weight, height, profile name, and date parsing validators with exhaustive edge cases.
"""

import pytest
from utils.validators import (
    validate_weight,
    validate_height,
    validate_username,
    validate_date_string,
    ValidationError,
)


class TestWeightValidation:
    """Tests weight validation constraints."""

    def test_valid_numeric_inputs(self):
        assert validate_weight(70.5) == 70.5
        assert validate_weight("68.2") == 68.2
        assert validate_weight("  85  ") == 85.0
        assert validate_weight(90) == 90.0

    def test_empty_or_whitespace_weight(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_weight("")
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_weight("   ")
        with pytest.raises(ValidationError, match="required"):
            validate_weight(None)

    def test_non_numeric_weight(self):
        with pytest.raises(ValidationError, match="not a valid number"):
            validate_weight("abc")
        with pytest.raises(ValidationError, match="not a valid number"):
            validate_weight("75kg")

    def test_negative_and_zero_weight(self):
        with pytest.raises(ValidationError, match="greater than zero"):
            validate_weight(0)
        with pytest.raises(ValidationError, match="greater than zero"):
            validate_weight("-10")

    def test_out_of_bounds_weight(self):
        with pytest.raises(ValidationError, match="at least 10.0 kg"):
            validate_weight(5.0)
        with pytest.raises(ValidationError, match="exceeds maximum"):
            validate_weight(550.0)


class TestHeightValidation:
    """Tests height validation constraints."""

    def test_valid_height_inputs(self):
        assert validate_height(1.75) == 1.75
        assert validate_height("1.825") == 1.825
        assert validate_height("  1.60  ") == 1.6
        assert validate_height(2.0) == 2.0

    def test_empty_or_whitespace_height(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_height("")
        with pytest.raises(ValidationError, match="required"):
            validate_height(None)

    def test_non_numeric_height(self):
        with pytest.raises(ValidationError, match="not a valid number"):
            validate_height("xyz")
        with pytest.raises(ValidationError, match="not a valid number"):
            validate_height("1.75m")

    def test_negative_and_zero_height(self):
        with pytest.raises(ValidationError, match="greater than zero"):
            validate_height(0)
        with pytest.raises(ValidationError, match="greater than zero"):
            validate_height("-1.8")

    def test_centimetre_detection_guidance(self):
        # 175 entered instead of 1.75
        with pytest.raises(ValidationError, match="Did you mean 1.75 m"):
            validate_height(175)

    def test_out_of_bounds_height(self):
        with pytest.raises(ValidationError, match="at least 0.50 metres"):
            validate_height(0.3)
        with pytest.raises(ValidationError, match="exceeds maximum"):
            validate_height(3.5)


class TestUsernameValidation:
    """Tests profile username validation."""

    def test_valid_usernames(self):
        assert validate_username("Arnav") == "Arnav"
        assert validate_username("Alex Smith") == "Alex Smith"
        assert validate_username("user_01") == "user_01"
        assert validate_username("  Sarah-Jane  ") == "Sarah-Jane"

    def test_empty_or_too_short(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_username("")
        with pytest.raises(ValidationError, match="at least 2 characters"):
            validate_username("A")

    def test_too_long(self):
        with pytest.raises(ValidationError, match="cannot exceed 32 characters"):
            validate_username("A" * 35)

    def test_invalid_characters(self):
        with pytest.raises(ValidationError, match="can only contain"):
            validate_username("User<script>")


class TestDateValidation:
    """Tests date string parsing."""

    def test_valid_date_formats(self):
        dt1 = validate_date_string("2026-11-14")
        assert dt1.year == 2026 and dt1.month == 11 and dt1.day == 14

        dt2 = validate_date_string("2026-11-14 14:30:00")
        assert dt2.hour == 14 and dt2.minute == 30

    def test_invalid_date_formats(self):
        with pytest.raises(ValidationError, match="Invalid date format"):
            validate_date_string("14-11-2026")
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_date_string("")
