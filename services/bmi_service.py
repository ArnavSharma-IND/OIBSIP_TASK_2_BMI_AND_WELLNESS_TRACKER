"""
BMI Domain Service
Coordinates calculation workflows, validation, persistence, and intelligent wellness insights.
"""

from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
from bmi_calculator import (
    calculate_bmi,
    classify_bmi,
    format_bmi,
    calculate_healthy_weight_range,
    get_category_editorial,
    DISCLAIMER_TEXT,
    CATEGORY_NORMAL,
)
from utils.validators import validate_weight, validate_height, ValidationError
from services.database_service import DatabaseService, db_service
from utils.helpers import format_display_date


class BMIService:
    """High-level service coordinating BMI calculations, record persistence, and insights."""

    def __init__(self, database_service: Optional[DatabaseService] = None):
        self.db_svc = database_service if database_service is not None else db_service

    def process_calculation(self, weight_input: Any, height_input: Any) -> Dict[str, Any]:
        """
        Validate inputs and compute unrounded BMI, rounded display value,
        classification category, healthy range, and editorial guidance.
        """
        w = validate_weight(weight_input)
        h = validate_height(height_input)

        raw_bmi = calculate_bmi(w, h)
        category = classify_bmi(raw_bmi)
        display_bmi = format_bmi(raw_bmi)
        min_healthy_w, max_healthy_w = calculate_healthy_weight_range(h)
        editorial = get_category_editorial(category)

        return {
            "weight": w,
            "height": h,
            "raw_bmi": raw_bmi,
            "bmi": float(display_bmi),
            "display_bmi": display_bmi,
            "category": category,
            "healthy_weight_range": (min_healthy_w, max_healthy_w),
            "editorial": editorial,
            "disclaimer": DISCLAIMER_TEXT,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def save_measurement(
        self,
        user_id: int,
        weight: float,
        height: float,
        bmi: float,
        category: str,
        recorded_at: Optional[str] = None,
    ) -> int:
        """Persist a measurement record to the database for the given user."""
        return self.db_svc.add_record(
            user_id=user_id,
            weight=weight,
            height=height,
            bmi=bmi,
            category=category,
            recorded_at=recorded_at,
        )

    def generate_insights(self, user_id: int) -> List[str]:
        """
        Generate contextual, non-clinical wellness insights derived from user history.
        Complies strictly with the requirement: screening context, no medical diagnosis.
        """
        records = self.db_svc.get_records_by_user(user_id=user_id, order="DESC")
        if not records:
            return [
                "Welcome to your wellness journey! Complete your first calculation to begin tracking your personal trends.",
                "Measurements recorded consistently over time provide the most helpful perspective on personal patterns.",
            ]

        insights: List[str] = []
        latest = records[0]
        count = len(records)

        # 1. Category-based screening observation
        latest_cat = latest["category"]
        if latest_cat == CATEGORY_NORMAL:
            insights.append("Your latest BMI is within the standard healthy reference range (18.5–24.9).")
        else:
            insights.append(
                f"Your latest measurement falls within the {latest_cat} category ({latest['bmi']:.2f})."
            )

        # 2. Delta comparison with previous record (if available)
        if count >= 2:
            prev = records[1]
            delta = round(latest["bmi"] - prev["bmi"], 2)
            prev_date = format_display_date(prev["recorded_at"], include_time=False)
            if abs(delta) < 0.01:
                insights.append(f"Your BMI remains stable compared with your previous entry on {prev_date}.")
            elif delta > 0:
                insights.append(
                    f"Your BMI increased by {delta:.2f} compared with your previous measurement on {prev_date}."
                )
            else:
                insights.append(
                    f"Your BMI decreased by {abs(delta):.2f} compared with your previous measurement on {prev_date}."
                )
        else:
            insights.append("Record regular measurements across several weeks to unlock directional trend insights.")

        # 3. History volume insight
        if count == 1:
            insights.append("Your profile contains 1 measurement recorded so far.")
        else:
            oldest = records[-1]
            oldest_date = format_display_date(oldest["recorded_at"], include_time=False)
            insights.append(f"Your profile contains {count} measurements recorded since {oldest_date}.")

        return insights


# Global BMI service instance
bmi_service = BMIService()
