"""Goal Validator: Robust input validation and integrity enforcement for financial goals."""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, Any, Optional

from app.models.goal import GoalCategoryEnum, GoalPriorityEnum


class GoalValidator:
    """Validates goal data to prevent invalid financial states or malformed inputs."""

    VALID_CATEGORIES = {e.value for e in GoalCategoryEnum}
    VALID_PRIORITIES = {e.value for e in GoalPriorityEnum}

    @classmethod
    def validate_goal_data(cls, data: Dict[str, Any], is_update: bool = False) -> Dict[str, Any]:
        """
        Validate and normalize goal dictionary.
        Raises ValueError with clear message if invalid.
        """
        cleaned: Dict[str, Any] = {}

        # 1. Name validation
        if "name" in data or not is_update:
            raw_name = data.get("name")
            if raw_name is None or not str(raw_name).strip():
                raise ValueError("Goal name is required and cannot be empty.")
            name_str = str(raw_name).strip()
            if len(name_str) > 150:
                raise ValueError("Goal name cannot exceed 150 characters.")
            cleaned["name"] = name_str

        # 2. Target Amount validation
        if "target_amount" in data or not is_update:
            raw_target = data.get("target_amount")
            if raw_target is None:
                raise ValueError("Target amount is required.")
            try:
                target_dec = Decimal(str(raw_target))
            except (InvalidOperation, TypeError, ValueError):
                raise ValueError("Target amount must be a valid positive number.")
            if target_dec <= Decimal("0.00"):
                raise ValueError("Target amount must be strictly greater than 0.")
            cleaned["target_amount"] = target_dec

        # 3. Current Amount validation
        if "current_amount" in data or not is_update:
            raw_current = data.get("current_amount", Decimal("0.00"))
            if raw_current is None:
                raw_current = Decimal("0.00")
            try:
                current_dec = Decimal(str(raw_current))
            except (InvalidOperation, TypeError, ValueError):
                raise ValueError("Current amount must be a valid non-negative number.")
            if current_dec < Decimal("0.00"):
                raise ValueError("Current amount cannot be negative.")
            cleaned["current_amount"] = current_dec

        # 4. Cross validation of current vs target amount
        target_val = cleaned.get("target_amount") or (Decimal(str(data.get("target_amount"))) if "target_amount" in data else None)
        current_val = cleaned.get("current_amount") or (Decimal(str(data.get("current_amount"))) if "current_amount" in data else None)
        if target_val is not None and current_val is not None and current_val > target_val:
            raise ValueError("Current amount cannot exceed the target amount.")

        # 5. Target Date validation
        if "target_date" in data or not is_update:
            raw_date = data.get("target_date")
            if raw_date is None:
                raise ValueError("Target date is required.")
            if isinstance(raw_date, date):
                t_date = raw_date
            elif isinstance(raw_date, datetime):
                t_date = raw_date.date()
            elif isinstance(raw_date, str):
                try:
                    t_date = date.fromisoformat(raw_date.strip())
                except ValueError:
                    raise ValueError("Target date must be in YYYY-MM-DD format.")
            else:
                raise ValueError("Invalid target date format.")

            if not is_update and t_date < date.today():
                raise ValueError("Target date must be today or in the future.")
            cleaned["target_date"] = t_date

        # 6. Category validation
        if "category" in data or not is_update:
            raw_cat = data.get("category", GoalCategoryEnum.SAVINGS.value)
            cat_str = str(raw_cat).strip().lower() if raw_cat else GoalCategoryEnum.SAVINGS.value
            if cat_str not in cls.VALID_CATEGORIES:
                raise ValueError(
                    f"Invalid category '{raw_cat}'. Supported categories: {', '.join(sorted(cls.VALID_CATEGORIES))}"
                )
            cleaned["category"] = cat_str

        # 7. Priority validation
        if "priority" in data or not is_update:
            raw_prio = data.get("priority", GoalPriorityEnum.MEDIUM.value)
            prio_str = str(raw_prio).strip().lower() if raw_prio else GoalPriorityEnum.MEDIUM.value
            if prio_str not in cls.VALID_PRIORITIES:
                raise ValueError(
                    f"Invalid priority '{raw_prio}'. Supported priorities: {', '.join(sorted(cls.VALID_PRIORITIES))}"
                )
            cleaned["priority"] = prio_str

        return cleaned
