"""Simulation Formatter: Formats simulation results into prompt-safe XML."""

import html
from typing import Dict, Any, Optional


class SimulationFormatter:
    """Escapes and formats what-if simulation data into XML for prompt context."""

    @staticmethod
    def _escape(val: Any) -> str:
        if val is None:
            return ""
        return html.escape(str(val), quote=True)

    @classmethod
    def format_simulation_xml(cls, sim_data: Optional[Dict[str, Any]]) -> str:
        """Format simulation result into <SIMULATION_CONTEXT> block."""
        if not sim_data:
            return "<SIMULATION_CONTEXT status=\"NONE\">\n  <!-- No active simulation -->\n</SIMULATION_CONTEXT>"

        scen = sim_data.get("scenario", "")
        cur = sim_data.get("current_state", {})
        sim = sim_data.get("simulated_state", {})
        impact = sim_data.get("impact", {})

        return (
            f"<SIMULATION_CONTEXT scenario=\"{cls._escape(scen)}\">\n"
            f"  <DISCLAIMER>HYPOTHETICAL SIMULATION ONLY — No modifications were made to database records.</DISCLAIMER>\n"
            f"  <CURRENT_STATE>\n"
            f"    <INCOME>₹{cur.get('monthly_income', 0.0):,.2f}</INCOME>\n"
            f"    <EXPENSES>₹{cur.get('monthly_expenses', 0.0):,.2f}</EXPENSES>\n"
            f"    <SAVINGS>₹{cur.get('monthly_savings', 0.0):,.2f}</SAVINGS>\n"
            f"    <SAVINGS_RATE>{cur.get('savings_rate_percentage', 0.0)}%</SAVINGS_RATE>\n"
            f"    <HEALTH_SCORE>{cur.get('health_score', 0.0)}</HEALTH_SCORE>\n"
            f"  </CURRENT_STATE>\n"
            f"  <SIMULATED_STATE>\n"
            f"    <INCOME>₹{sim.get('monthly_income', 0.0):,.2f}</INCOME>\n"
            f"    <EXPENSES>₹{sim.get('monthly_expenses', 0.0):,.2f}</EXPENSES>\n"
            f"    <SAVINGS>₹{sim.get('monthly_savings', 0.0):,.2f}</SAVINGS>\n"
            f"    <SAVINGS_RATE>{sim.get('savings_rate_percentage', 0.0)}%</SAVINGS_RATE>\n"
            f"    <HEALTH_SCORE>{sim.get('health_score', 0.0)}</HEALTH_SCORE>\n"
            f"  </SIMULATED_STATE>\n"
            f"  <IMPACT>\n"
            f"    <DELTA_SAVINGS>₹{impact.get('delta_monthly_savings', 0.0):+,.2f}</DELTA_SAVINGS>\n"
            f"    <DELTA_SAVINGS_RATE>{impact.get('delta_savings_rate', 0.0):+.1f}%</DELTA_SAVINGS_RATE>\n"
            f"    <DELTA_HEALTH_SCORE>{impact.get('delta_health_score', 0.0):+.1f}</DELTA_HEALTH_SCORE>\n"
            f"    <SUMMARY>{cls._escape(impact.get('summary', ''))}</SUMMARY>\n"
            f"  </IMPACT>\n"
            f"</SIMULATION_CONTEXT>"
        )
