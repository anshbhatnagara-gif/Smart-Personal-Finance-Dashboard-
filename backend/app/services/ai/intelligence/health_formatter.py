"""Health Formatter: Formats financial health score and components into prompt-safe XML."""

import html
from typing import Dict, Any, Optional


class HealthFormatter:
    """Escapes and formats health score data into prompt XML."""

    @staticmethod
    def _escape(val: Any) -> str:
        if val is None:
            return ""
        return html.escape(str(val), quote=True)

    @classmethod
    def format_health_xml(cls, health_data: Optional[Dict[str, Any]]) -> str:
        """Format health score and 7 components into <FINANCIAL_HEALTH_SCORE> block."""
        if not health_data or health_data.get("overall_score") is None:
            return (
                "<FINANCIAL_HEALTH_SCORE status=\"INSUFFICIENT_DATA\">\n"
                "  <!-- Insufficient verified financial data to calculate financial health score -->\n"
                "</FINANCIAL_HEALTH_SCORE>"
            )

        score = health_data.get("overall_score")
        status = health_data.get("status", "GOOD")
        summary = health_data.get("summary", "")
        components = health_data.get("components", {})

        lines = [
            f"<FINANCIAL_HEALTH_SCORE score=\"{score}\" status=\"{cls._escape(status)}\">",
            f"  <SUMMARY>{cls._escape(summary)}</SUMMARY>",
            "  <COMPONENTS>"
        ]

        for k, comp in components.items():
            c_score = comp.get("score")
            c_status = comp.get("status", "INSUFFICIENT_DATA")
            c_weight = comp.get("weight", 0.0)
            c_ev = comp.get("verified_evidence", "")
            c_expl = comp.get("calculation_explanation", "")

            score_attr = f" score=\"{c_score}\"" if c_score is not None else ""
            lines.append(
                f"    <COMPONENT name=\"{cls._escape(k)}\" status=\"{cls._escape(c_status)}\"{score_attr} weight=\"{c_weight}\">\n"
                f"      <EVIDENCE>{cls._escape(c_ev)}</EVIDENCE>\n"
                f"      <EXPLANATION>{cls._escape(c_expl)}</EXPLANATION>\n"
                f"    </COMPONENT>"
            )

        lines.append("  </COMPONENTS>")
        lines.append("</FINANCIAL_HEALTH_SCORE>")

        return "\n".join(lines)
