"""
Unit Tests for BMI Calculation and Classification
Verifies exact clinical thresholds, numerical precision, unrounded categorization, and error handling.
"""

import pytest
from bmi_calculator import (
    calculate_bmi,
    classify_bmi,
    format_bmi,
    calculate_healthy_weight_range,
    CATEGORY_UNDERWEIGHT,
    CATEGORY_NORMAL,
    CATEGORY_OVERWEIGHT,
    CATEGORY_OBESE,
)


class TestBMICalculation:
    """Verifies the core mathematical BMI formula: Weight (kg) / Height (m)^2."""

    def test_standard_calculation(self):
        # 70 kg at 1.75 m -> 70 / (1.75^2) = 22.85714...
        bmi = calculate_bmi(70, 1.75)
        assert pytest.approx(bmi, rel=1e-3) == 22.857
        assert format_bmi(bmi) == "22.86"

    def test_exact_integer_inputs(self):
        # 80 kg at 2.0 m -> 80 / 4 = 20.0
        assert calculate_bmi(80, 2.0) == 20.0
        assert format_bmi(20.0) == "20.00"

    def test_small_and_large_sensible_values(self):
        # Light weight
        bmi_light = calculate_bmi(45, 1.65)
        assert bmi_light > 0

        # Heavy weight
        bmi_heavy = calculate_bmi(120, 1.80)
        assert bmi_heavy > 0

    def test_zero_and_negative_weight_rejected(self):
        with pytest.raises(ValueError, match="Weight must be greater than zero"):
            calculate_bmi(0, 1.75)

        with pytest.raises(ValueError, match="Weight must be greater than zero"):
            calculate_bmi(-70, 1.75)

    def test_zero_and_negative_height_rejected(self):
        with pytest.raises(ValueError, match="Height must be greater than zero"):
            calculate_bmi(70, 0)

        with pytest.raises(ValueError, match="Height must be greater than zero"):
            calculate_bmi(70, -1.75)

    def test_none_and_invalid_types(self):
        with pytest.raises(ValueError):
            calculate_bmi(None, 1.75)

        with pytest.raises(ValueError):
            calculate_bmi("not_a_number", 1.75)


class TestBMIClassification:
    """Verifies strict WHO classification boundaries using exact unrounded values."""

    def test_underweight_boundary(self):
        assert classify_bmi(10.0) == CATEGORY_UNDERWEIGHT
        assert classify_bmi(18.49) == CATEGORY_UNDERWEIGHT
        assert classify_bmi(18.4999) == CATEGORY_UNDERWEIGHT

    def test_normal_boundary(self):
        # Exact lower boundary: 18.5
        assert classify_bmi(18.5) == CATEGORY_NORMAL
        assert classify_bmi(20.0) == CATEGORY_NORMAL
        assert classify_bmi(24.9) == CATEGORY_NORMAL
        assert classify_bmi(24.9999) == CATEGORY_NORMAL

    def test_overweight_boundary(self):
        # Exact lower boundary: 25.0
        assert classify_bmi(25.0) == CATEGORY_OVERWEIGHT
        assert classify_bmi(27.5) == CATEGORY_OVERWEIGHT
        assert classify_bmi(29.9) == CATEGORY_OVERWEIGHT
        assert classify_bmi(29.9999) == CATEGORY_OVERWEIGHT

    def test_obese_boundary(self):
        # Exact lower boundary: 30.0
        assert classify_bmi(30.0) == CATEGORY_OBESE
        assert classify_bmi(30.01) == CATEGORY_OBESE
        assert classify_bmi(45.0) == CATEGORY_OBESE

    def test_unrounded_boundary_safety(self):
        # 24.996 should classify as Normal, not Overweight despite rounding to 25.00 for display
        bmi_val = 24.996
        assert classify_bmi(bmi_val) == CATEGORY_NORMAL
        assert format_bmi(bmi_val) == "25.00"

        # 25.001 should classify as Overweight
        assert classify_bmi(25.001) == CATEGORY_OVERWEIGHT


class TestHealthyWeightRange:
    """Verifies healthy weight range derivation based on BMI 18.5 - 24.9."""

    def test_healthy_range_computation(self):
        min_w, max_w = calculate_healthy_weight_range(1.80)
        # 18.5 * (1.8^2) = 18.5 * 3.24 = 59.94 -> 59.9 kg
        # 24.9 * (1.8^2) = 24.9 * 3.24 = 80.676 -> 80.7 kg
        assert pytest.approx(min_w, abs=0.2) == 59.9
        assert pytest.approx(max_w, abs=0.2) == 80.7

    def test_invalid_height_for_range(self):
        with pytest.raises(ValueError):
            calculate_healthy_weight_range(0)
