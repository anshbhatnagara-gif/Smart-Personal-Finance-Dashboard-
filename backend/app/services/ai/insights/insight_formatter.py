"""Insight Formatter: Safe dictionary formatting and prompt context delimiters."""

import re
from typing import List, Dict, Any


class InsightFormatter:
    """Utilities for structuring, sanitizing, and formatting proactive insights."""

    @staticmethod
    def sanitize_text(text: str) -> str:
        """Strip prompt injection attempts and enforce string safety."""
        if not text:
            return ""
        # Remove XML/HTML tags and instruction-like overrides
        clean = re.sub(r"<[^>]*>", "", text)
        clean = clean.replace("\n", " ").replace("\r", " ")
        return clean.strip()[:300]

    @staticmethod
    def format_currency_inr(amount: float) -> str:
        """Format floating point amount to INR string."""
        return f"₹{amount:,.2f}"

    @staticmethod
    def format_for_prompt_context(insights: List[Dict[str, Any]]) -> str:
        """Format insights into delimited XML block for AI system instruction context."""
        if not insights:
            return "<PROACTIVE_FINANCIAL_INSIGHTS>\nNo proactive alerts or insights active for the current period.\n</PROACTIVE_FINANCIAL_INSIGHTS>"

        lines = ["<PROACTIVE_FINANCIAL_INSIGHTS>"]
        for idx, item in enumerate(insights, 1):
            severity = item.get("severity", "info").upper()
            title = InsightFormatter.sanitize_text(item.get("title", ""))
            msg = InsightFormatter.sanitize_text(item.get("message", ""))
            rec = InsightFormatter.sanitize_text(item.get("recommendation", ""))
            lines.append(f"{idx}. [{severity}] {title}: {msg} | Recommendation: {rec}")

        lines.append("</PROACTIVE_FINANCIAL_INSIGHTS>")
        return "\n".join(lines)
