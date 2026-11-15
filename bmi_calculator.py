"""
Core BMI Calculation Engine
Implements mathematically rigorous BMI calculations, standard WHO classification logic,
healthy weight range estimation, and informational guidance.
"""

from typing import Tuple, Dict, Any


# Standard WHO BMI Boundaries
BOUND_UNDERWEIGHT = 18.5
BOUND_NORMAL_MAX = 25.0  # [18.5, 25.0) -> Normal (often written 18.5 - 24.9)
BOUND_OVERWEIGHT_MAX = 30.0  # [25.0, 30.0) -> Overweight (often written 25.0 - 29.9)

CATEGORY_UNDERWEIGHT = "Underweight"
CATEGORY_NORMAL = "Normal"
CATEGORY_OVERWEIGHT = "Overweight"
CATEGORY_OBESE = "Obese"

# Health disclaimer as requested
DISCLAIMER_TEXT = (
    "BMI is an informational screening measure based on height and weight. "
    "It does not directly measure body fat percentage or muscle composition and "
    "should not be construed as a complete medical diagnosis."
)


def calculate_bmi(weight: float, height: float) -> float:
    """
    Calculate Body Mass Index (BMI) using standard metric units.

    Formula:
        BMI = Weight (kg) / [Height (m)]²

    Args:
        weight: Body weight in kilograms (must be strictly > 0).
        height: Stature in metres (must be strictly > 0).

    Returns:
        float: Exact unrounded Body Mass Index value.

    Raises:
        ValueError: If weight or height is non-positive.
    """
    if weight is None or height is None:
        raise ValueError("Weight and height must not be None.")

    try:
        w = float(weight)
        h = float(height)
    except (TypeError, ValueError) as err:
        raise ValueError(f"Weight and height must be numeric values: {err}")

    if w <= 0:
        raise ValueError("Weight must be greater than zero.")

    if h <= 0:
        raise ValueError("Height must be greater than zero.")

    return w / (h ** 2)


def classify_bmi(bmi: float) -> str:
    """
    Classify Body Mass Index according to standard clinical thresholds.
    CRITICAL: Uses the exact unrounded BMI to prevent boundary misclassification.

    Classification Table:
        BMI < 18.5           -> Underweight
        18.5 <= BMI < 25.0   -> Normal
        25.0 <= BMI < 30.0   -> Overweight
        BMI >= 30.0          -> Obese

    Args:
        bmi: Exact unrounded Body Mass Index value.

    Returns:
        str: Classification category name.
    """
    if bmi is None:
        raise ValueError("BMI value cannot be None.")

    try:
        val = float(bmi)
    except (TypeError, ValueError) as err:
        raise ValueError(f"BMI must be a numeric value: {err}")

    if val < BOUND_UNDERWEIGHT:
        return CATEGORY_UNDERWEIGHT
    elif val < BOUND_NORMAL_MAX:
        return CATEGORY_NORMAL
    elif val < BOUND_OVERWEIGHT_MAX:
        return CATEGORY_OVERWEIGHT
    else:
        return CATEGORY_OBESE


def format_bmi(bmi: float) -> str:
    """Format BMI value rounded to two decimal places for presentation."""
    return f"{bmi:.2f}"


def calculate_healthy_weight_range(height: float) -> Tuple[float, float]:
    """
    Compute the healthy weight boundary (kg) for a given height (m),
    corresponding to the Normal BMI range of 18.5 to 24.99.
    """
    if height <= 0:
        raise ValueError("Height must be greater than zero.")
    min_weight = 18.5 * (height ** 2)
    max_weight = 24.9 * (height ** 2)
    return round(min_weight, 1), round(max_weight, 1)


def get_category_editorial(category: str) -> Dict[str, Any]:
    """
    Return informational editorial context for a given BMI category.
    Avoids clinical prescription, emphasizes healthy sustainable habits.
    """
    data = {
        CATEGORY_UNDERWEIGHT: {
            "summary": "Below standard reference range",
            "guidance": (
                "Your BMI is currently below 18.5. Consider nutrient-dense whole foods "
                "and gradual strength development. Consult a registered healthcare "
                "professional if this reflects unintentional weight loss."
            ),
            "range_label": "< 18.5",
        },
        CATEGORY_NORMAL: {
            "summary": "Within healthy reference range",
            "guidance": (
                "Your BMI is within the healthy reference zone (18.5–24.9). "
                "Continue maintaining consistent physical activity, balanced nutrition, "
                "and mindful hydration to support sustained vitality."
            ),
            "range_label": "18.5 – 24.9",
        },
        CATEGORY_OVERWEIGHT: {
            "summary": "Above standard reference range",
            "guidance": (
                "Your BMI is currently between 25.0 and 29.9. Sustainable daily movement, "
                "quality sleep, and mindful caloric balance can help support long-term "
                "cardiovascular and metabolic wellness."
            ),
            "range_label": "25.0 – 29.9",
        },
        CATEGORY_OBESE: {
            "summary": "Elevated reference range",
            "guidance": (
                "Your BMI is 30.0 or above. Structured lifestyle adaptations, personalized "
                "nutrition, and collaboration with a physician or dietitian can provide "
                "supportive, evidence-based health guidance."
            ),
            "range_label": "≥ 30.0",
        },
    }
    return data.get(
        category,
        {
            "summary": "Reference range assessment",
            "guidance": "Regular measurements help track personal wellness patterns over time.",
            "range_label": "-",
        },
    )
