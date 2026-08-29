"""Action Formatter: Formats verified action proposals and audit context into prompt-safe XML."""

import html
from typing import List, Dict, Any, Optional
from app.models.smart_action import SmartActionProposal


class ActionFormatter:
    """Safely escapes and renders smart actions into XML tags for AI system context."""

    @staticmethod
    def _escape(text: Any) -> str:
        """Escape angle brackets and ampersands."""
        if text is None:
            return ""
        return html.escape(str(text), quote=True)

    @classmethod
    def format_actions_xml(cls, actions: List[Any]) -> str:
        """
        Format list of SmartActionProposal models or action dictionaries into <SMART_ACTIONS> block.
        """
        if not actions:
            return "<SMART_ACTIONS count=\"0\">\n  <!-- No pending or active smart action recommendations -->\n</SMART_ACTIONS>"

        lines = [f"<SMART_ACTIONS count=\"{len(actions)}\">"]

        for a in actions:
            # Support both ORM models and dictionaries
            if hasattr(a, "action_id"):
                action_id = a.action_id
                action_type = a.action_type
                title = a.title
                status = a.status
                risk_level = a.risk_level
                evidence = a.verified_evidence
                amount = float(a.financial_amount)
                impact = a.expected_impact
                req_conf = a.requires_confirmation
            else:
                action_id = a.get("action_id", "")
                action_type = a.get("action_type", "")
                title = a.get("title", "")
                status = a.get("status", "PROPOSED")
                risk_level = a.get("risk_level", "MEDIUM")
                evidence = a.get("verified_evidence", "")
                amount = float(a.get("financial_amount", 0.0))
                impact = a.get("expected_impact", "")
                req_conf = a.get("requires_confirmation", True)

            lines.append(
                f"  <ACTION id=\"{cls._escape(action_id)}\" type=\"{cls._escape(action_type)}\" status=\"{cls._escape(status)}\" risk=\"{cls._escape(risk_level)}\">\n"
                f"    <TITLE>{cls._escape(title)}</TITLE>\n"
                f"    <VERIFIED_EVIDENCE>{cls._escape(evidence)}</VERIFIED_EVIDENCE>\n"
                f"    <PROPOSED_AMOUNT currency=\"INR\">₹{amount:,.2f}</PROPOSED_AMOUNT>\n"
                f"    <EXPECTED_IMPACT>{cls._escape(impact)}</EXPECTED_IMPACT>\n"
                f"    <REQUIRES_CONFIRMATION>{'true' if req_conf else 'false'}</REQUIRES_CONFIRMATION>\n"
                f"  </ACTION>"
            )

        lines.append("</SMART_ACTIONS>")
        return "\n".join(lines)
