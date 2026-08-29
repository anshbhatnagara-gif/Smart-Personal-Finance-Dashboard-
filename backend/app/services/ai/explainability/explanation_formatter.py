"""Explanation Formatter: Formats structured explanations into prompt-safe XML."""

import html
from typing import List, Dict, Any, Optional


class ExplanationFormatter:
    """Safely escapes and renders explainability records into XML."""

    @staticmethod
    def _escape(val: Any) -> str:
        if val is None:
            return ""
        return html.escape(str(val), quote=True)

    @classmethod
    def format_explanations_xml(cls, explanations: Optional[List[Dict[str, Any]]]) -> str:
        """Format explanations into <FINANCIAL_EXPLANATIONS> block."""
        if not explanations:
            return "<FINANCIAL_EXPLANATIONS count=\"0\">\n  <!-- No active explanations available -->\n</FINANCIAL_EXPLANATIONS>"

        lines = [f"<FINANCIAL_EXPLANATIONS count=\"{len(explanations)}\">"]

        for exp in explanations:
            exp_type = exp.get("explanation_type", "")
            title = exp.get("title", "")
            summary = exp.get("summary", "")
            ev = exp.get("verified_evidence", "")
            basis = exp.get("calculation_basis", "")
            conf = exp.get("confidence", "HIGH")
            lim = exp.get("limitations", "")

            lines.append(
                f"  <EXPLANATION type=\"{cls._escape(exp_type)}\" confidence=\"{cls._escape(conf)}\">\n"
                f"    <TITLE>{cls._escape(title)}</TITLE>\n"
                f"    <SUMMARY>{cls._escape(summary)}</SUMMARY>\n"
                f"    <VERIFIED_EVIDENCE>{cls._escape(ev)}</VERIFIED_EVIDENCE>\n"
                f"    <CALCULATION_BASIS>{cls._escape(basis)}</CALCULATION_BASIS>\n"
                f"    <LIMITATIONS>{cls._escape(lim)}</LIMITATIONS>\n"
                f"  </EXPLANATION>"
            )

        lines.append("</FINANCIAL_EXPLANATIONS>")
        return "\n".join(lines)
