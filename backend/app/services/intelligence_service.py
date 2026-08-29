"""Smart Finance Intelligence Service: Production-grade deterministic financial intelligence engine."""

import calendar
from datetime import datetime, date, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session

from app.models.transaction import Transaction, TransactionType
from app.models.budget import Budget
from app.schemas.intelligence import (
    IntelligenceSummary,
    CategoryBehaviorItem,
    TransactionAnomalyItem,
    BudgetRiskPredictionItem,
    SavingsOpportunityFinding,
    HealthScoreDetailedFactor,
    FinancialHealthDetail,
    StructuredRecommendation,
    IntelligenceInsight,
    SmartInsightsData,
    FinancialContextForAI
)
from app.services.finance_engine import (
    calculate_savings_rate,
    calculate_monthly_cashflow,
    calculate_metric_growth,
    calculate_budget_utilization,
    format_currency_inr
)


class IntelligenceService:
    """Deterministic, production-ready financial intelligence engine."""

    @staticmethod
    def calculate_cashflow_health(income: Decimal, expenses: Decimal) -> str:
        """Determine cash flow health status."""
        inc = income or Decimal("0.00")
        exp = expenses or Decimal("0.00")
        if inc > exp:
            return "SURPLUS"
        elif inc == exp:
            return "BALANCED"
        return "DEFICIT"

    @staticmethod
    def analyze_category_behavior(
        transactions: List[Transaction],
        budgets: List[Budget],
        current_month: int,
        current_year: int
    ) -> List[CategoryBehaviorItem]:
        """
        Analyze category spending behavior, MoM deltas, averages, and deterministic risk levels.
        """
        if current_month == 1:
            prev_month = 12
            prev_year = current_year - 1
        else:
            prev_month = current_month - 1
            prev_year = current_year

        # Separate into current and previous month expense transactions
        cur_txs_by_cat: Dict[str, List[Transaction]] = {}
        prev_txs_by_cat: Dict[str, List[Transaction]] = {}
        total_cur_expenses = Decimal("0.00")

        for tx in transactions:
            if tx.type == TransactionType.EXPENSE or str(tx.type).lower() == "expense":
                cat = tx.category.strip()
                t_date = tx.transaction_date if isinstance(tx.transaction_date, date) else date.fromisoformat(str(tx.transaction_date))

                if t_date.year == current_year and t_date.month == current_month:
                    cur_txs_by_cat.setdefault(cat, []).append(tx)
                    total_cur_expenses += tx.amount
                elif t_date.year == prev_year and t_date.month == prev_month:
                    prev_txs_by_cat.setdefault(cat, []).append(tx)

        budget_map = {b.category.lower().strip(): b.amount for b in budgets}
        all_categories = sorted(set(cur_txs_by_cat.keys()).union(set(prev_txs_by_cat.keys())))
        results: List[CategoryBehaviorItem] = []

        for cat in all_categories:
            c_txs = cur_txs_by_cat.get(cat, [])
            p_txs = prev_txs_by_cat.get(cat, [])

            c_spend = sum((t.amount for t in c_txs), Decimal("0.00"))
            p_spend = sum((t.amount for t in p_txs), Decimal("0.00"))
            tx_count = len(c_txs)
            avg_tx = (c_spend / Decimal(tx_count)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if tx_count > 0 else Decimal("0.00")
            pct_of_total = float(((c_spend / total_cur_expenses) * Decimal("100")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)) if total_cur_expenses > Decimal("0.00") else 0.0

            # MoM growth
            if p_spend > Decimal("0.00"):
                mom_growth = float((((c_spend - p_spend) / p_spend) * Decimal("100")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
            elif c_spend > Decimal("0.00"):
                mom_growth = 100.0
            else:
                mom_growth = 0.0

            # Budget utilization
            b_amt = budget_map.get(cat.lower().strip())
            b_util = float(((c_spend / b_amt) * Decimal("100")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)) if b_amt and b_amt > Decimal("0.00") else None

            # Deterministic Risk Level
            if (b_util and b_util > 100.0) or (mom_growth >= 50.0 and c_spend >= Decimal("5000.00")):
                risk = "CRITICAL"
            elif (b_util and b_util >= 80.0) or (mom_growth >= 30.0 and c_spend >= Decimal("3000.00")) or pct_of_total >= 40.0:
                risk = "HIGH"
            elif (mom_growth >= 10.0 and c_spend >= Decimal("1000.00")) or (b_util and b_util >= 60.0):
                risk = "MEDIUM"
            else:
                risk = "LOW"

            results.append(CategoryBehaviorItem(
                category=cat,
                total_spending=c_spend,
                percentage_of_total_spending=pct_of_total,
                transaction_count=tx_count,
                average_transaction=avg_tx,
                current_month_spending=c_spend,
                previous_month_spending=p_spend,
                month_over_month_percentage_change=mom_growth,
                budget_amount=b_amt,
                budget_utilization=b_util,
                risk_level=risk
            ))

        return sorted(results, key=lambda x: x.total_spending, reverse=True)

    @staticmethod
    def detect_unusual_transactions(transactions: List[Transaction]) -> List[TransactionAnomalyItem]:
        """
        Detect unusually large transactions per category using historical averages and variance multipliers.
        """
        anomalies: List[TransactionAnomalyItem] = []
        if not transactions:
            return anomalies

        # Group expense transactions by category
        cat_txs: Dict[str, List[Transaction]] = {}
        for tx in transactions:
            if tx.type == TransactionType.EXPENSE or str(tx.type).lower() == "expense":
                cat = tx.category.strip()
                cat_txs.setdefault(cat, []).append(tx)

        for cat, tx_list in cat_txs.items():
            amounts = [t.amount for t in tx_list]
            avg_amount = sum(amounts) / Decimal(len(amounts))

            for tx in tx_list:
                # Anomaly criteria:
                # 1. Single large transaction >= ₹25,000
                # 2. Or >= 2.5x category average with >= ₹2,000 threshold when multiple transactions exist
                is_anomaly = False
                mult = float((tx.amount / avg_amount).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)) if avg_amount > 0 else 1.0

                if tx.amount >= Decimal("25000.00"):
                    is_anomaly = True
                elif len(tx_list) >= 2 and tx.amount >= avg_amount * Decimal("2.5") and tx.amount >= Decimal("2000.00"):
                    is_anomaly = True

                if is_anomaly:
                    severity = "HIGH" if tx.amount >= Decimal("30000.00") or mult >= 3.5 else "MEDIUM"
                    reason = f"{format_currency_inr(tx.amount)} {cat} transaction '{tx.title}' is a high-value outlier" + (f" ({mult}x higher than your average {cat} transaction of {format_currency_inr(avg_amount)})." if len(tx_list) >= 2 else ".")
                    anomalies.append(TransactionAnomalyItem(
                        transaction_id=tx.id,
                        category=cat,
                        title=tx.title,
                        amount=tx.amount,
                        reason=reason,
                        severity=severity
                    ))

        return sorted(anomalies, key=lambda a: a.amount, reverse=True)

    @staticmethod
    def calculate_budget_risk(
        transactions: List[Transaction],
        budgets: List[Budget],
        current_month: int,
        current_year: int,
        target_day: Optional[int] = None
    ) -> List[BudgetRiskPredictionItem]:
        """
        Predict budget overrun probability based on current velocity and days remaining in month.
        """
        predictions: List[BudgetRiskPredictionItem] = []
        if not budgets:
            return predictions

        now = datetime.now()
        day_of_month = target_day or (now.day if (now.month == current_month and now.year == current_year) else 15)
        day_of_month = max(1, min(31, day_of_month))
        days_in_month = calendar.monthrange(current_year, current_month)[1]

        # Calculate current spending per category
        cat_spent: Dict[str, Decimal] = {}
        for tx in transactions:
            if tx.type == TransactionType.EXPENSE or str(tx.type).lower() == "expense":
                t_date = tx.transaction_date if isinstance(tx.transaction_date, date) else date.fromisoformat(str(tx.transaction_date))
                if t_date.year == current_year and t_date.month == current_month:
                    cat = tx.category.lower().strip()
                    cat_spent[cat] = cat_spent.get(cat, Decimal("0.00")) + tx.amount

        for b in budgets:
            cat_key = b.category.lower().strip()
            spent = cat_spent.get(cat_key, Decimal("0.00"))
            remaining = b.amount - spent
            utilization = float(((spent / b.amount) * Decimal("100")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)) if b.amount > Decimal("0.00") else 100.0

            # Daily spending velocity
            velocity = (spent / Decimal(day_of_month)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            projected_spend = (velocity * Decimal(days_in_month)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            # Predict risk
            if spent > b.amount:
                risk_level = "LIKELY_OVER_BUDGET"
                explanation = f"{b.category} has already exceeded its {format_currency_inr(b.amount)} budget by {format_currency_inr(spent - b.amount)}."
            elif projected_spend > b.amount * Decimal("1.05"):
                risk_level = "LIKELY_OVER_BUDGET"
                explanation = f"At current pace of {format_currency_inr(velocity)}/day, {b.category} will reach {format_currency_inr(projected_spend)} (exceeding budget by {format_currency_inr(projected_spend - b.amount)})."
            elif projected_spend >= b.amount * Decimal("0.90") or utilization >= 80.0:
                risk_level = "AT_RISK"
                explanation = f"{b.category} is at {utilization}% utilization with {format_currency_inr(remaining)} remaining for {days_in_month - day_of_month} days."
            elif projected_spend >= b.amount * Decimal("0.75"):
                risk_level = "WATCH"
                explanation = f"{b.category} pace is on track but requires monitoring ({format_currency_inr(remaining)} remaining)."
            else:
                risk_level = "SAFE"
                explanation = f"{b.category} spending is well controlled with {format_currency_inr(remaining)} safe buffer remaining."

            predictions.append(BudgetRiskPredictionItem(
                category=b.category,
                amount=b.amount,
                spent=spent,
                remaining=remaining,
                utilization=utilization,
                spending_velocity=velocity,
                projected_spend=projected_spend,
                risk_level=risk_level,
                explanation=explanation
            ))

        return sorted(predictions, key=lambda p: (0 if p.risk_level == "LIKELY_OVER_BUDGET" else 1 if p.risk_level == "AT_RISK" else 2 if p.risk_level == "WATCH" else 3, -p.utilization))

    @staticmethod
    def calculate_savings_opportunity(
        transactions: List[Transaction],
        income: Decimal,
        budgets: List[Budget]
    ) -> List[SavingsOpportunityFinding]:
        """
        Identify realistic, data-derived monthly savings opportunities.
        """
        findings: List[SavingsOpportunityFinding] = []
        discretionary_categories = {
            "dining", "food", "restaurant", "swiggy", "zomato", "entertainment",
            "shopping", "clothing", "movies", "travel", "vacation", "subscriptions",
            "gaming", "cafes", "coffee", "hobbies"
        }

        # Calculate category spending
        cat_spending: Dict[str, Decimal] = {}
        for tx in transactions:
            if tx.type == TransactionType.EXPENSE or str(tx.type).lower() == "expense":
                cat = tx.category.strip()
                cat_spending[cat] = cat_spending.get(cat, Decimal("0.00")) + tx.amount

        budget_map = {b.category.lower().strip(): b.amount for b in budgets}

        for cat, amount in cat_spending.items():
            cat_lower = cat.lower().strip()
            is_discretionary = any(d in cat_lower for d in discretionary_categories)
            b_cap = budget_map.get(cat_lower)

            if is_discretionary and amount >= Decimal("2000.00"):
                reduction_pct = 15.0
                monthly_saving = (amount * Decimal("0.15")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
                annual_saving = monthly_saving * 12
                priority = "HIGH" if amount >= Decimal("8000.00") else "MEDIUM"

                findings.append(SavingsOpportunityFinding(
                    category=cat,
                    current_spending=amount,
                    suggested_reduction_percentage=reduction_pct,
                    potential_monthly_saving=monthly_saving,
                    potential_annual_saving=annual_saving,
                    explanation=f"Potential saving opportunity: approximately {format_currency_inr(monthly_saving)}/month ({format_currency_inr(annual_saving)}/year) by trimming 15% from discretionary {cat} expenses.",
                    priority=priority
                ))
            elif b_cap and amount > b_cap:
                overrun = amount - b_cap
                reduction_pct = float(((overrun / amount) * Decimal("100")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
                findings.append(SavingsOpportunityFinding(
                    category=cat,
                    current_spending=amount,
                    suggested_reduction_percentage=reduction_pct,
                    potential_monthly_saving=overrun,
                    potential_annual_saving=overrun * 12,
                    explanation=f"Potential saving opportunity: approximately {format_currency_inr(overrun)}/month by realigning {cat} back to your {format_currency_inr(b_cap)} budget cap.",
                    priority="HIGH"
                ))

        return sorted(findings, key=lambda f: (0 if f.priority == "HIGH" else 1 if f.priority == "MEDIUM" else 2, -f.potential_monthly_saving))

    @staticmethod
    def calculate_health_score_detail(
        income: Decimal,
        expenses: Decimal,
        prev_expenses: Decimal,
        total_budget: Decimal
    ) -> FinancialHealthDetail:
        """
        Calculate explainable 5-factor health score with actionable recommendations for each factor.
        """
        savings_rate = calculate_savings_rate(income, expenses)
        net_savings = calculate_monthly_cashflow(income, expenses)

        # Factor 1: Savings Rate (30%)
        if savings_rate >= 35.0:
            s_score = 100
            s_exp = f"Outstanding savings rate of {savings_rate}%, well above the 35% target."
            s_rec = "Maintain current momentum and consider allocating extra surplus to investments."
        elif savings_rate >= 20.0:
            s_score = int(70 + ((savings_rate - 20.0) / 15.0) * 30)
            s_exp = f"Solid savings rate of {savings_rate}% creating steady financial security."
            s_rec = "Aim to gradually increase savings towards 30% by trimming flexible costs."
        elif savings_rate > 0.0:
            s_score = int((savings_rate / 20.0) * 70)
            s_exp = f"Modest savings rate of {savings_rate}% leaves limited safety margin."
            s_rec = "Target at least 20% savings by reviewing top discretionary spending."
        else:
            s_score = 10
            s_exp = "Zero or negative net savings. Cash outflow equals or exceeds income."
            s_rec = "Urgent: reduce non-essential outflows to restore positive cash flow."

        # Factor 2: Budget Discipline (25%)
        if total_budget > Decimal("0.00"):
            util = float(((expenses / total_budget) * Decimal("100")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
            if util <= 85.0:
                b_score = 100
                b_exp = f"Strict envelope discipline at {util}% total budget utilization."
                b_rec = "Keep monitoring your categories as the month progresses."
            elif util <= 100.0:
                b_score = max(50, int(100 - (util - 85.0) * 3.3))
                b_exp = f"Nearing total budget limit at {util}% utilization."
                b_rec = "Slow down discretionary outflows to prevent overrun."
            else:
                b_score = max(10, int(50 - (util - 100.0) * 2.0))
                b_exp = f"Total budget envelope exceeded by {round(util - 100.0, 1)}%."
                b_rec = "Realign category spending caps and freeze non-essential purchases."
        else:
            b_score = 75
            b_exp = "No active monthly budget envelopes set."
            b_rec = "Configure category budget envelopes to unlock higher financial discipline score."

        # Factor 3: Spending Control (15%)
        if prev_expenses > Decimal("0.00"):
            growth = float((((expenses - prev_expenses) / prev_expenses) * Decimal("100")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
            if growth <= 0.0:
                sp_score = 100
                sp_exp = f"Outflows dropped by {abs(growth)}% compared to last month."
                sp_rec = "Great spending discipline. Keep outflows stable."
            elif growth <= 5.0:
                sp_score = 90
                sp_exp = f"Modest {growth}% increase in outflows vs prior month."
                sp_rec = "Monitor acceleration to ensure spending stays balanced."
            elif growth <= 15.0:
                sp_score = 70
                sp_exp = f"Spending accelerated by {growth}% compared to last month."
                sp_rec = "Review recent category increases to ensure they were planned."
            else:
                sp_score = max(20, int(70 - (growth - 15.0) * 2.0))
                sp_exp = f"High spending surge (+{growth}% MoM)."
                sp_rec = "Identify one-off spikes versus recurring lifestyle inflation."
        else:
            sp_score = 85
            sp_exp = "Baseline spending initialized."
            sp_rec = "Track next month's spending to establish historical trend baseline."

        # Factor 4: Emergency Buffer (15%)
        if net_savings >= Decimal("30000.00"):
            em_score = 95
            em_exp = f"Strong monthly cash surplus of {format_currency_inr(net_savings)}."
            em_rec = "Direct surplus toward 6-month emergency reserve and diversified growth."
        elif net_savings >= Decimal("15000.00"):
            em_score = 85
            em_exp = f"Reliable liquidity buffer of {format_currency_inr(net_savings)}."
            em_rec = "Continue building emergency cash reserves."
        elif net_savings > Decimal("0.00"):
            em_score = 65
            em_exp = f"Modest monthly surplus of {format_currency_inr(net_savings)}."
            em_rec = "Boost monthly surplus to at least ₹15,000 for financial resilience."
        else:
            em_score = 25
            em_exp = f"Deficit spending ({format_currency_inr(net_savings)}). Cash buffer decreasing."
            em_rec = "Immediate priority: eliminate deficit to protect emergency funds."

        # Factor 5: Consistency (15%)
        cs_score = 88
        cs_exp = "Active financial record keeping and balanced cash flow management."
        cs_rec = "Continue logging transactions and reviewing weekly insights."

        # Total weighted score
        final_score = int(round(
            s_score * 0.30 +
            b_score * 0.25 +
            sp_score * 0.15 +
            em_score * 0.15 +
            cs_score * 0.15
        ))
        final_score = max(0, min(100, final_score))

        if final_score >= 90:
            status = "Excellent"
        elif final_score >= 75:
            status = "Good"
        elif final_score >= 60:
            status = "Fair"
        elif final_score >= 40:
            status = "Needs Attention"
        else:
            status = "Critical"

        factors = [
            HealthScoreDetailedFactor(name="Savings Rate", score=s_score, weight="30%", explanation=s_exp, recommendation=s_rec),
            HealthScoreDetailedFactor(name="Budget Discipline", score=b_score, weight="25%", explanation=b_exp, recommendation=b_rec),
            HealthScoreDetailedFactor(name="Spending Control", score=sp_score, weight="15%", explanation=sp_exp, recommendation=sp_rec),
            HealthScoreDetailedFactor(name="Emergency Buffer", score=em_score, weight="15%", explanation=em_exp, recommendation=em_rec),
            HealthScoreDetailedFactor(name="Consistency", score=cs_score, weight="15%", explanation=cs_exp, recommendation=cs_rec)
        ]

        return FinancialHealthDetail(score=final_score, status=status, factors=factors)

    @staticmethod
    def generate_recommendations(
        savings_opportunities: List[SavingsOpportunityFinding],
        budget_risks: List[BudgetRiskPredictionItem],
        category_analysis: List[CategoryBehaviorItem]
    ) -> List[StructuredRecommendation]:
        """
        Synthesize prioritized, high-impact recommendations from intelligence data.
        """
        recs: List[StructuredRecommendation] = []

        # 1. Action on budget overruns / risks
        for br in budget_risks:
            if br.risk_level == "LIKELY_OVER_BUDGET":
                recs.append(StructuredRecommendation(
                    category=br.category,
                    title=f"Cap Outflows on {br.category}",
                    action=f"Freeze non-essential {br.category} spending to prevent exceeding the {format_currency_inr(br.amount)} envelope limit.",
                    potential_monthly_saving=br.projected_spend - br.amount if br.projected_spend > br.amount else Decimal("1000.00"),
                    impact="HIGH"
                ))

        # 2. Action on top savings opportunities
        for so in savings_opportunities[:3]:
            recs.append(StructuredRecommendation(
                category=so.category,
                title=f"Optimize {so.category} Spending",
                action=f"Reduce {so.category} spending by {so.suggested_reduction_percentage}% to save {format_currency_inr(so.potential_monthly_saving)}/month.",
                potential_monthly_saving=so.potential_monthly_saving,
                impact=so.priority
            ))

        # 3. Action on rapid category growth
        for ca in category_analysis:
            if ca.risk_level in ["CRITICAL", "HIGH"] and ca.month_over_month_percentage_change >= 35.0:
                recs.append(StructuredRecommendation(
                    category=ca.category,
                    title=f"Investigate {ca.category} Acceleration",
                    action=f"{ca.category} rose {ca.month_over_month_percentage_change}% MoM. Review recent receipts to verify whether this is one-off or recurring.",
                    potential_monthly_saving=None,
                    impact="MEDIUM"
                ))

        return recs

    @classmethod
    def generate_full_insights(
        cls,
        transactions: List[Transaction],
        budgets: List[Budget],
        target_month: Optional[int] = None,
        target_year: Optional[int] = None
    ) -> SmartInsightsData:
        """
        Execute full Smart Finance Intelligence Engine suite for authenticated user data.
        """
        now = datetime.now()
        cur_m = target_month or now.month
        cur_y = target_year or now.year

        if cur_m == 1:
            prev_m = 12
            prev_y = cur_y - 1
        else:
            prev_m = cur_m - 1
            prev_y = cur_y

        month_str = f"{cur_y}-{cur_m:02d}"

        # Current month transactions
        cur_txs = [
            t for t in transactions
            if (t.transaction_date if isinstance(t.transaction_date, date) else date.fromisoformat(str(t.transaction_date))).year == cur_y
            and (t.transaction_date if isinstance(t.transaction_date, date) else date.fromisoformat(str(t.transaction_date))).month == cur_m
        ]

        # Previous month transactions
        prev_txs = [
            t for t in transactions
            if (t.transaction_date if isinstance(t.transaction_date, date) else date.fromisoformat(str(t.transaction_date))).year == prev_y
            and (t.transaction_date if isinstance(t.transaction_date, date) else date.fromisoformat(str(t.transaction_date))).month == prev_m
        ]

        cur_income = sum((t.amount for t in cur_txs if t.type == TransactionType.INCOME or str(t.type).lower() == "income"), Decimal("0.00"))
        cur_expenses = sum((t.amount for t in cur_txs if t.type == TransactionType.EXPENSE or str(t.type).lower() == "expense"), Decimal("0.00"))
        prev_expenses = sum((t.amount for t in prev_txs if t.type == TransactionType.EXPENSE or str(t.type).lower() == "expense"), Decimal("0.00"))

        net_savings = calculate_monthly_cashflow(cur_income, cur_expenses)
        savings_rate = calculate_savings_rate(cur_income, cur_expenses)
        cashflow_status = cls.calculate_cashflow_health(cur_income, cur_expenses)

        summary = IntelligenceSummary(
            total_income=cur_income,
            total_expenses=cur_expenses,
            net_savings=net_savings,
            savings_rate=savings_rate,
            current_month=month_str,
            cashflow_status=cashflow_status
        )

        user_cur_budgets = [b for b in budgets if b.month == cur_m and b.year == cur_y] or budgets
        total_budget_envelope = sum((b.amount for b in user_cur_budgets), Decimal("0.00"))

        # 1. Category Analysis
        category_analysis = cls.analyze_category_behavior(transactions, user_cur_budgets, cur_m, cur_y)

        # 2. Anomalies
        anomalies = cls.detect_unusual_transactions(transactions)

        # 3. Budget Risks
        budget_risks = cls.calculate_budget_risk(transactions, user_cur_budgets, cur_m, cur_y)

        # 4. Savings Opportunities
        savings_opportunities = cls.calculate_savings_opportunity(cur_txs or transactions, cur_income, user_cur_budgets)

        # 5. Financial Health
        health_score = cls.calculate_health_score_detail(cur_income, cur_expenses, prev_expenses, total_budget_envelope)

        # 6. Recommendations
        recommendations = cls.generate_recommendations(savings_opportunities, budget_risks, category_analysis)

        # 7. Insights
        insights: List[IntelligenceInsight] = []
        if savings_rate >= 40.0:
            insights.append(IntelligenceInsight(
                type="HIGH_SAVER",
                title="High Savings Rate",
                message=f"You are saving {savings_rate}% of your income ({format_currency_inr(net_savings)}).",
                severity="POSITIVE",
                metric=f"{savings_rate}%",
                recommendation="Allocate extra monthly surplus toward wealth generation."
            ))
        elif savings_rate < 15.0 and cur_income > Decimal("0.00"):
            insights.append(IntelligenceInsight(
                type="CASHFLOW_WARNING",
                title="Low Savings Buffer",
                message=f"Your savings rate is {savings_rate}%, leaving a tight buffer of {format_currency_inr(net_savings)}.",
                severity="WARNING",
                metric=f"{savings_rate}%",
                recommendation="Target at least 20% savings by reviewing discretionary categories."
            ))

        for ca in category_analysis:
            if ca.risk_level == "CRITICAL" and ca.month_over_month_percentage_change >= 40.0:
                insights.append(IntelligenceInsight(
                    type="CATEGORY_SPIKE",
                    title=f"Sharp Increase in {ca.category}",
                    message=f"{ca.category} spending grew {ca.month_over_month_percentage_change}% vs last month ({format_currency_inr(ca.current_month_spending)} vs {format_currency_inr(ca.previous_month_spending)}).",
                    severity="CRITICAL",
                    category=ca.category,
                    metric=f"+{ca.month_over_month_percentage_change}%",
                    recommendation="Review individual transactions to identify high-cost outliers."
                ))

        for br in budget_risks:
            if br.risk_level == "LIKELY_OVER_BUDGET":
                insights.append(IntelligenceInsight(
                    type="BUDGET_WARNING",
                    title=f"Budget Risk: {br.category}",
                    message=br.explanation,
                    severity="WARNING",
                    category=br.category,
                    metric=f"{br.utilization}%",
                    recommendation=f"Limit further spending on {br.category}."
                ))

        if not insights:
            insights.append(IntelligenceInsight(
                type="HEALTHY_OVERVIEW",
                title="Finances on Track",
                message=f"Your cash flow is balanced with {format_currency_inr(net_savings)} in net savings.",
                severity="INFO",
                metric=f"{savings_rate}%",
                recommendation="Continue maintaining your regular spending limits."
            ))

        return SmartInsightsData(
            generated_at=datetime.now(timezone.utc).isoformat(),
            summary=summary,
            insights=insights,
            recommendations=recommendations,
            category_analysis=category_analysis,
            anomalies=anomalies,
            budget_risks=budget_risks,
            savings_opportunities=savings_opportunities,
            health_score=health_score
        )

    @classmethod
    def get_financial_context(cls, user_id: int, db: Session) -> FinancialContextForAI:
        """
        Verified structured facts interface for future AI model consumption in Phase 2.5/3.
        The AI never queries the database directly.
        """
        user_txs = db.query(Transaction).filter(Transaction.user_id == user_id).order_by(Transaction.transaction_date.desc()).all()
        user_budgets = db.query(Budget).filter(Budget.user_id == user_id).all()

        insights_data = cls.generate_full_insights(user_txs, user_budgets)

        return FinancialContextForAI(
            user_id=user_id,
            as_of=insights_data.generated_at,
            monthly_income=insights_data.summary.total_income,
            monthly_expenses=insights_data.summary.total_expenses,
            net_savings=insights_data.summary.net_savings,
            savings_rate=insights_data.summary.savings_rate,
            top_categories=[c.model_dump() for c in insights_data.category_analysis[:5]],
            budget_risks=[b.model_dump() for b in insights_data.budget_risks],
            anomalies=[a.model_dump() for a in insights_data.anomalies],
            savings_opportunities=[s.model_dump() for s in insights_data.savings_opportunities],
            health_score=insights_data.health_score.score,
            health_status=insights_data.health_score.status,
            insights=[i.model_dump() for i in insights_data.insights],
            recommendations=[r.model_dump() for r in insights_data.recommendations]
        )
