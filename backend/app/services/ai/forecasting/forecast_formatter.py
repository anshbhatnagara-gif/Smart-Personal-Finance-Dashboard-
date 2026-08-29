"""Forecast Formatter: Converts deterministic forecasts into safe XML prompt blocks."""

import html
from typing import Dict, Any


class ForecastFormatter:
    """Safely escapes and renders deterministic forecasts within XML tags."""

    @staticmethod
    def _escape(val: Any) -> str:
        if val is None:
            return ""
        s = str(val).replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")
        return s

    @classmethod
    def format_forecast_xml(cls, forecast_data: Dict[str, Any]) -> str:
        """
        Generate <FINANCIAL_FORECASTS> and <FORECAST_LIMITATIONS> XML blocks.
        """
        if not forecast_data.get("is_sufficient_data"):
            return (
                "<FINANCIAL_FORECASTS status=\"INSUFFICIENT_DATA\">\n"
                "  <NOTE>Insufficient verified transaction history to generate forward-looking projections.</NOTE>\n"
                "</FINANCIAL_FORECASTS>\n"
                "<FORECAST_LIMITATIONS>\n"
                "  <LIMITATION>At least one full month of recorded transaction history is required for projections.</LIMITATION>\n"
                "</FORECAST_LIMITATIONS>"
            )

        inc = forecast_data.get("income_forecast", {})
        exp = forecast_data.get("expense_forecast", {})
        sav = forecast_data.get("savings_forecast", {})

        xml = [
            f"<FINANCIAL_FORECASTS confidence=\"{cls._escape(sav.get('confidence'))}\">",
            "  <SUMMARY>",
            f"    <PROJECTED_INCOME amount=\"{inc.get('projected_value', 0.0):.2f}\" trend=\"{inc.get('trend_percentage', 0.0):+.1f}%\" />",
            f"    <PROJECTED_EXPENSES amount=\"{exp.get('projected_value', 0.0):.2f}\" trend=\"{exp.get('trend_percentage', 0.0):+.1f}%\" />",
            f"    <PROJECTED_NET_SAVINGS amount=\"{sav.get('projected_value', 0.0):.2f}\" savings_rate=\"{sav.get('projected_savings_rate_percentage', 0.0):.1f}%\" />",
            "  </SUMMARY>",
            "  <CATEGORY_EXPENSE_FORECASTS>"
        ]

        for cat, c_data in exp.get("category_forecasts", {}).items():
            xml.append(
                f"    <CATEGORY name=\"{cls._escape(cat)}\" "
                f"projected=\"{c_data.get('projected_spending', 0.0):.2f}\" "
                f"current=\"{c_data.get('current_spending', 0.0):.2f}\" "
                f"trend=\"{c_data.get('trend_percentage', 0.0):+.1f}%\" />"
            )

        xml.append("  </CATEGORY_EXPENSE_FORECASTS>")

        # Budget exhaustion
        burn_list = forecast_data.get("budget_exhaustion_forecast", [])
        if burn_list:
            xml.append("  <BUDGET_BURNS>")
            for b in burn_list:
                xml.append(
                    f"    <BUDGET category=\"{cls._escape(b['category'])}\" "
                    f"budget=\"{b['budget_amount']:.2f}\" "
                    f"projected_spend=\"{b['projected_month_end_spending']:.2f}\" "
                    f"will_exceed=\"{str(b['will_exceed_budget']).lower()}\" />"
                )
            xml.append("  </BUDGET_BURNS>")

        # Goal completion
        goal_list = forecast_data.get("goal_completion_forecast", [])
        if goal_list:
            xml.append("  <GOAL_PROJECTIONS>")
            for g in goal_list:
                xml.append(
                    f"    <GOAL name=\"{cls._escape(g['name'])}\" "
                    f"target=\"{g['target_amount']:.2f}\" "
                    f"remaining=\"{g['remaining_amount']:.2f}\" "
                    f"status=\"{cls._escape(g['status'])}\" "
                    f"target_date=\"{cls._escape(g['target_date'])}\" />"
                )
            xml.append("  </GOAL_PROJECTIONS>")

        xml.append("</FINANCIAL_FORECASTS>")

        # Limitations
        xml.append("<FORECAST_LIMITATIONS>")
        xml.append(f"  <LIMITATION>{cls._escape(inc.get('limitations'))}</LIMITATION>")
        xml.append(f"  <LIMITATION>{cls._escape(exp.get('limitations'))}</LIMITATION>")
        xml.append(f"  <LIMITATION>{cls._escape(sav.get('limitations'))}</LIMITATION>")
        xml.append("</FORECAST_LIMITATIONS>")

        return "\n".join(xml)
