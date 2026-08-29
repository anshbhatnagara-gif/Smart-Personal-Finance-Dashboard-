"""Prediction Formatter: Converts predictive insights into safe XML prompt blocks."""

from typing import Dict, Any, List


class PredictionFormatter:
    """Safely escapes and renders predictive insights inside <PREDICTIVE_INSIGHTS> XML tags."""

    @staticmethod
    def _escape(val: Any) -> str:
        if val is None:
            return ""
        s = str(val).replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")
        return s

    @classmethod
    def format_predictions_xml(cls, predictions: List[Dict[str, Any]]) -> str:
        """Generate <PREDICTIVE_INSIGHTS> XML block."""
        if not predictions:
            return (
                "<PREDICTIVE_INSIGHTS count=\"0\">\n"
                "  <NOTE>No predictive alerts or forward-looking insights at this time.</NOTE>\n"
                "</PREDICTIVE_INSIGHTS>"
            )

        xml = [
            f"<PREDICTIVE_INSIGHTS count=\"{len(predictions)}\">"
        ]

        for p in predictions:
            xml.append(
                f"  <PREDICTION category=\"{cls._escape(p.get('category'))}\" "
                f"severity=\"{cls._escape(p.get('severity'))}\" "
                f"type=\"{cls._escape(p.get('prediction_type'))}\">"
            )
            xml.append(f"    <TITLE>{cls._escape(p.get('title'))}</TITLE>")
            xml.append(f"    <VERIFIED_FACT>{cls._escape(p.get('verified_fact'))}</VERIFIED_FACT>")
            xml.append(f"    <FORECAST>{cls._escape(p.get('forecast'))}</FORECAST>")
            xml.append(f"    <RISK>{cls._escape(p.get('risk'))}</RISK>")
            xml.append(f"    <AI_SUGGESTION>{cls._escape(p.get('ai_suggestion'))}</AI_SUGGESTION>")
            xml.append("  </PREDICTION>")

        xml.append("</PREDICTIVE_INSIGHTS>")
        return "\n".join(xml)
