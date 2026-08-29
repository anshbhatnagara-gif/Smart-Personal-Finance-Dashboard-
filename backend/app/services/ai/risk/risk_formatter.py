"""Risk Formatter: Converts deterministic financial risk evaluations into safe XML blocks."""

from typing import Dict, Any, List


class RiskFormatter:
    """Safely escapes and renders financial risk factors in <FINANCIAL_RISKS> XML tags."""

    @staticmethod
    def _escape(val: Any) -> str:
        if val is None:
            return ""
        s = str(val).replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")
        return s

    @classmethod
    def format_risks_xml(cls, risk_data: Dict[str, Any]) -> str:
        """Generate <FINANCIAL_RISKS> XML block."""
        risks: List[Dict[str, Any]] = risk_data.get("risks", [])
        stress = risk_data.get("stress_summary", {})
        overall_level = stress.get("overall_risk_level", "NONE")

        if not risks:
            return (
                f"<FINANCIAL_RISKS overall_level=\"{cls._escape(overall_level)}\" total_risks=\"0\">\n"
                "  <NOTE>No active financial risks or budget vulnerabilities detected.</NOTE>\n"
                "</FINANCIAL_RISKS>"
            )

        xml = [
            f"<FINANCIAL_RISKS overall_level=\"{cls._escape(overall_level)}\" total_risks=\"{len(risks)}\">"
        ]

        for r in risks:
            xml.append(
                f"  <RISK type=\"{cls._escape(r.get('risk_type'))}\" "
                f"severity=\"{cls._escape(r.get('severity'))}\" "
                f"affected_amount=\"{r.get('affected_amount', 0.0):.2f}\">"
            )
            xml.append(f"    <TITLE>{cls._escape(r.get('title'))}</TITLE>")
            xml.append(f"    <MESSAGE>{cls._escape(r.get('message'))}</MESSAGE>")
            xml.append(f"    <EVIDENCE>{cls._escape(r.get('verified_evidence'))}</EVIDENCE>")
            xml.append(f"    <ACTION>{cls._escape(r.get('recommended_action'))}</ACTION>")
            xml.append("  </RISK>")

        xml.append("</FINANCIAL_RISKS>")
        return "\n".join(xml)
