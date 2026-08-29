"""Forecasting rules, confidence calculations, and deterministic extrapolation methodologies."""

from decimal import Decimal
from typing import List, Dict, Any, Tuple


class ForecastConfidence:
    """Standardized confidence classifications."""
    HIGH = "HIGH"          # >= 3 months of verified historical data
    MEDIUM = "MEDIUM"      # 1 to 2 months of verified historical data
    LOW = "LOW"            # Sub-month historical sample
    INSUFFICIENT = "INSUFFICIENT_DATA"  # 0 or negligible data


class ForecastRules:
    """Deterministic mathematical rules for trend extrapolation and moving averages."""

    @staticmethod
    def calculate_confidence(months_count: int, transaction_count: int) -> str:
        """Determine forecast confidence based on verified data depth."""
        if months_count == 0 or transaction_count == 0:
            return ForecastConfidence.INSUFFICIENT
        if months_count >= 3 and transaction_count >= 3:
            return ForecastConfidence.HIGH
        if months_count >= 1 and transaction_count >= 1:
            return ForecastConfidence.MEDIUM
        return ForecastConfidence.LOW

    @staticmethod
    def calculate_weighted_average(monthly_values: List[Decimal]) -> Decimal:
        """
        Calculate linearly weighted moving average placing higher weight on recent periods.
        If empty, returns Decimal(0.00).
        """
        if not monthly_values:
            return Decimal("0.00")
        if len(monthly_values) == 1:
            return monthly_values[0].quantize(Decimal("0.01"))

        weights = list(range(1, len(monthly_values) + 1))
        total_weight = sum(weights)
        weighted_sum = sum(val * w for val, w in zip(monthly_values, weights))
        result = weighted_sum / Decimal(str(total_weight))
        return result.quantize(Decimal("0.01"))

    @staticmethod
    def calculate_trend_rate(monthly_values: List[Decimal]) -> float:
        """
        Calculate period-over-period average growth percentage.
        Returns 0.0 if insufficient points.
        """
        if len(monthly_values) < 2:
            return 0.0
        
        rates = []
        for i in range(1, len(monthly_values)):
            prev = monthly_values[i - 1]
            curr = monthly_values[i]
            if prev > Decimal("0.00"):
                rates.append(float((curr - prev) / prev * Decimal("100.0")))
            elif curr > Decimal("0.00"):
                rates.append(100.0)
            else:
                rates.append(0.0)
                
        return round(sum(rates) / len(rates), 2)
