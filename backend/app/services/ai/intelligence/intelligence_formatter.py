"""Intelligence Formatter: Aggregates all AI intelligence domains into master <FINANCIAL_INTELLIGENCE> XML."""

import html
from typing import Dict, Any, Optional

from app.services.ai.intelligence.health_formatter import HealthFormatter
from app.services.ai.explainability.explanation_formatter import ExplanationFormatter
from app.services.ai.automation.action_formatter import ActionFormatter


class IntelligenceFormatter:
    """Master XML formatter for complete financial intelligence context."""

    @staticmethod
    def _escape(val: Any) -> str:
        if val is None:
            return ""
        return html.escape(str(val), quote=True)

    @classmethod
    def format_master_intelligence_xml(cls, intelligence_data: Dict[str, Any]) -> str:
        """Format aggregated intelligence payload into structured <FINANCIAL_INTELLIGENCE> block."""
        health_xml = HealthFormatter.format_health_xml(intelligence_data.get("health_score"))
        exp_xml = ExplanationFormatter.format_explanations_xml(intelligence_data.get("explanations", []))
        actions_xml = ActionFormatter.format_actions_xml(intelligence_data.get("smart_actions", []))

        forecast_data = intelligence_data.get("forecast", {})
        risk_data = intelligence_data.get("risks", {})
        goals_data = intelligence_data.get("goals", [])

        # Format forecasts sub-block
        fc_lines = [
            "<FORECASTS status=\"ESTIMATED\">",
            f"  <PROJECTED_INCOME>₹{forecast_data.get('projected_income', 0.0):,.2f}</PROJECTED_INCOME>",
            f"  <PROJECTED_EXPENSES>₹{forecast_data.get('projected_expenses', 0.0):,.2f}</PROJECTED_EXPENSES>",
            f"  <PROJECTED_SAVINGS>₹{forecast_data.get('projected_net_savings', 0.0):,.2f}</PROJECTED_SAVINGS>",
            f"  <PROJECTED_SAVINGS_RATE>{forecast_data.get('projected_savings_rate_percentage', 0.0):.1f}%</PROJECTED_SAVINGS_RATE>",
            f"  <CONFIDENCE>{cls._escape(forecast_data.get('confidence', 'MEDIUM'))}</CONFIDENCE>",
            "</FORECASTS>"
        ]

        # Format risks sub-block
        r_list = risk_data.get("risks", [])
        risk_lines = [f"<RISKS count=\"{len(r_list)}\" stress_level=\"{cls._escape(risk_data.get('stress_summary', {}).get('status', 'NONE'))}\">"]
        for r in r_list:
            risk_lines.append(
                f"  <RISK type=\"{cls._escape(r.get('risk_type'))}\" severity=\"{cls._escape(r.get('severity'))}\">\n"
                f"    <TITLE>{cls._escape(r.get('title'))}</TITLE>\n"
                f"    <MESSAGE>{cls._escape(r.get('message'))}</MESSAGE>\n"
                f"  </RISK>"
            )
        risk_lines.append("</RISKS>")

        # Format goals sub-block
        goal_lines = [f"<GOALS count=\"{len(goals_data)}\">"]
        for g in goals_data:
            goal_lines.append(
                f"  <GOAL name=\"{cls._escape(g.get('name'))}\" status=\"{cls._escape(g.get('status'))}\" progress=\"{g.get('progress_percentage', 0.0):.1f}%\">\n"
                f"    <TARGET_AMOUNT>₹{g.get('target_amount', 0.0):,.2f}</TARGET_AMOUNT>\n"
                f"    <CURRENT_AMOUNT>₹{g.get('current_amount', 0.0):,.2f}</CURRENT_AMOUNT>\n"
                f"    <REQUIRED_MONTHLY>₹{g.get('required_monthly_contribution', 0.0):,.2f}</REQUIRED_MONTHLY>\n"
                f"  </GOAL>"
            )
        goal_lines.append("</GOALS>")

        return (
            "<FINANCIAL_INTELLIGENCE>\n"
            f"{health_xml}\n"
            f"{chr(10).join(fc_lines)}\n"
            f"{chr(10).join(risk_lines)}\n"
            f"{chr(10).join(goal_lines)}\n"
            f"{actions_xml}\n"
            f"{exp_xml}\n"
            "</FINANCIAL_INTELLIGENCE>"
        )
