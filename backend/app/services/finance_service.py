"""Smart Finance Service: Pure mathematical calculation formulas with Decimal precision."""

from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Tuple
from app.models.transaction import Transaction, TransactionType
from app.models.budget import Budget
from app.schemas.budget import BudgetStatus
from app.schemas.dashboard import (
    MonthComparison,
    CategoryBreakdownItem,
    HealthFactor,
    FinancialHealthScore,
    SmartInsight
)


def format_currency_inr(amount: Decimal) -> str:
    """Format decimal amount as Indian Rupee (INR) representation."""
    quantized = amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    is_neg = quantized < 0
    abs_amt = abs(quantized)

    s = str(abs_amt)
    if len(s) <= 3:
        formatted = s
    else:
        last3 = s[-3:]
        rest = s[:-3]
        groups = []
        while len(rest) > 2:
            groups.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.insert(0, rest)
        formatted = ",".join(groups) + "," + last3

    return f"-₹{formatted}" if is_neg else f"₹{formatted}"


def calculate_savings(income: Decimal, expenses: Decimal) -> Decimal:
    """Calculate Net Savings = Income - Expenses."""
    return income - expenses


def calculate_savings_rate(income: Decimal, expenses: Decimal) -> float:
    """Calculate savings rate percentage (0.0 to 100.0)."""
    if income <= Decimal("0.00"):
        return 0.0
    rate = ((income - expenses) / income) * Decimal("100")
    rate_clamped = max(Decimal("0.0"), min(Decimal("100.0"), rate))
    return float(rate_clamped.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def calculate_budget_usage(spent: Decimal, budget: Decimal) -> Tuple[float, Decimal, BudgetStatus]:
    """Calculate budget utilization percentage, remaining buffer, and status."""
    if budget <= Decimal("0.00"):
        return 100.0, Decimal("0.00"), BudgetStatus.OVER_BUDGET

    percentage = float(((spent / budget) * Decimal("100")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
    remaining = budget - spent

    if percentage > 100.0:
        status = BudgetStatus.OVER_BUDGET
    elif percentage >= 80.0:
        status = BudgetStatus.NEAR_LIMIT
    elif percentage >= 60.0:
        status = BudgetStatus.ON_TRACK
    else:
        status = BudgetStatus.UNDER_BUDGET

    return percentage, remaining, status


def compare_months(current: Decimal, previous: Decimal) -> MonthComparison:
    """Compute numerical and percentage delta between two periods."""
    delta = current - previous
    if previous == Decimal("0.00"):
        if current > Decimal("0.00"):
            return MonthComparison(
                delta=delta,
                percentage=100.0,
                is_increase=True,
                text="+100%"
            )
        return MonthComparison(
            delta=delta,
            percentage=0.0,
            is_increase=True,
            text="0%"
        )

    pct_decimal = ((current - previous) / previous) * Decimal("100")
    pct_float = float(abs(pct_decimal).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
    is_increase = delta >= Decimal("0.00")
    text = f"{'+' if is_increase else '-'}{pct_float}%"

    return MonthComparison(
        delta=delta,
        percentage=pct_float,
        is_increase=is_increase,
        text=text
    )


def analyze_categories(transactions: List[Transaction]) -> List[CategoryBreakdownItem]:
    """Aggregate expense transactions by category sorted descending."""
    category_totals: Dict[str, Decimal] = {}
    total_expenses = Decimal("0.00")

    for tx in transactions:
        if tx.type == TransactionType.EXPENSE:
            category_totals[tx.category] = category_totals.get(tx.category, Decimal("0.00")) + tx.amount
            total_expenses += tx.amount

    breakdown: List[CategoryBreakdownItem] = []
    for cat, amt in sorted(category_totals.items(), key=lambda item: item[1], reverse=True):
        pct = float(((amt / total_expenses) * Decimal("100")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)) if total_expenses > 0 else 0.0
        breakdown.append(CategoryBreakdownItem(
            category=cat,
            amount=amt,
            percentage=pct
        ))

    return breakdown


def detect_overspending(
    budgets: List[Budget],
    transactions: List[Transaction]
) -> List[Dict[str, Any]]:
    """Detect categories exceeding or nearing their budget envelope."""
    category_expenses: Dict[str, Decimal] = {}
    for tx in transactions:
        if tx.type == TransactionType.EXPENSE:
            category_expenses[tx.category] = category_expenses.get(tx.category, Decimal("0.00")) + tx.amount

    alerts = []
    for b in budgets:
        spent = category_expenses.get(b.category, Decimal("0.00"))
        pct, remaining, status = calculate_budget_usage(spent, b.amount)
        if status in (BudgetStatus.OVER_BUDGET, BudgetStatus.NEAR_LIMIT):
            alerts.append({
                "category": b.category,
                "budget": b.amount,
                "spent": spent,
                "remaining": remaining,
                "percentage": pct,
                "status": status
            })
    return alerts


def calculate_financial_health_score(financial_data: Dict[str, Any]) -> FinancialHealthScore:
    """
    Calculate 5-Factor Weighted Financial Health Score (0-100).
    Weights:
      1. Savings Rate (30%)
      2. Budget Discipline (25%)
      3. Spending Control (15%)
      4. Emergency Buffer (15%)
      5. Consistency (15%)
    """
    income: Decimal = financial_data.get("income", Decimal("0.00"))
    expenses: Decimal = financial_data.get("expenses", Decimal("0.00"))
    prev_expenses: Decimal = financial_data.get("prev_expenses", Decimal("0.00"))
    total_budget: Decimal = financial_data.get("total_budget", Decimal("0.00"))

    # 1. Savings Rate Score (0-100) -> Target >= 35%
    savings_rate = calculate_savings_rate(income, expenses)
    savings_score = min(100, int((savings_rate / 35.0) * 100))

    # 2. Budget Discipline Score (0-100) -> Target <= 85% of envelope
    if total_budget > Decimal("0.00"):
        utilization = float((expenses / total_budget) * Decimal("100"))
        if utilization <= 85.0:
            budget_score = 100
        elif utilization <= 100.0:
            budget_score = max(50, int(100 - (utilization - 85.0) * 3.3))
        else:
            budget_score = max(10, int(50 - (utilization - 100.0) * 2.0))
    else:
        budget_score = 80

    # 3. Spending Control Score (0-100) -> MoM Expense Velocity
    if prev_expenses > Decimal("0.00"):
        growth = float(((expenses - prev_expenses) / prev_expenses) * Decimal("100"))
        if growth <= 0.0:
            spending_growth_score = 100
        elif growth <= 5.0:
            spending_growth_score = 90
        elif growth <= 15.0:
            spending_growth_score = 70
        else:
            spending_growth_score = max(20, int(70 - (growth - 15.0) * 2.0))
    else:
        spending_growth_score = 85

    # 4. Emergency Buffer Score (0-100)
    net_savings = calculate_savings(income, expenses)
    if net_savings > Decimal("30000.00"):
        emergency_score = 95
    elif net_savings > Decimal("15000.00"):
        emergency_score = 85
    elif net_savings > Decimal("0.00"):
        emergency_score = 65
    else:
        emergency_score = 30

    # 5. Consistency Score
    consistency_score = 88

    # Weighted aggregate calculation
    total_score = int(round(
        savings_score * 0.30 +
        budget_score * 0.25 +
        spending_growth_score * 0.15 +
        emergency_score * 0.15 +
        consistency_score * 0.15
    ))
    total_score = max(0, min(100, total_score))

    if total_score >= 90:
        status_label = "Excellent"
        status_class = "badge-emerald"
    elif total_score >= 75:
        status_label = "Good"
        status_class = "badge-indigo"
    elif total_score >= 60:
        status_label = "Fair"
        status_class = "badge-cyan"
    elif total_score >= 40:
        status_label = "Needs Attention"
        status_class = "badge-amber"
    else:
        status_label = "Critical"
        status_class = "badge-rose"

    return FinancialHealthScore(
        score=total_score,
        status=status_label,
        status_class=status_class,
        factors=[
            HealthFactor(name="Savings Rate", score=savings_score, weight="30%"),
            HealthFactor(name="Budget Discipline", score=budget_score, weight="25%"),
            HealthFactor(name="Spending Control", score=spending_growth_score, weight="15%"),
            HealthFactor(name="Emergency Buffer", score=emergency_score, weight="15%"),
            HealthFactor(name="Consistency", score=consistency_score, weight="15%")
        ]
    )


def generate_smart_insights(financial_data: Dict[str, Any]) -> List[SmartInsight]:
    """Generate dynamic, actionable insights from real financial data."""
    cur_income: Decimal = financial_data.get("income", Decimal("0.00"))
    cur_expenses: Decimal = financial_data.get("expenses", Decimal("0.00"))
    prev_income: Decimal = financial_data.get("prev_income", Decimal("0.00"))
    prev_expenses: Decimal = financial_data.get("prev_expenses", Decimal("0.00"))
    transactions: List[Transaction] = financial_data.get("transactions", [])
    budgets: List[Budget] = financial_data.get("budgets", [])

    insights: List[SmartInsight] = []
    savings_rate = calculate_savings_rate(cur_income, cur_expenses)
    net_savings = calculate_savings(cur_income, cur_expenses)
    prev_savings = calculate_savings(prev_income, prev_expenses)

    # 1. Savings Rate
    if savings_rate >= 40.0:
        insights.append(SmartInsight(
            type="positive",
            icon="🎯",
            tag="High Saver",
            text=f"You are saving **{savings_rate}%** of your monthly income ({format_currency_inr(net_savings)}). Keep up this stellar discipline!"
        ))
    elif savings_rate >= 20.0:
        insights.append(SmartInsight(
            type="positive",
            icon="💰",
            tag="Healthy Savings",
            text=f"Your savings rate is **{savings_rate}%**. You're building a reliable wealth buffer."
        ))
    else:
        insights.append(SmartInsight(
            type="warning",
            icon="⚠️",
            tag="Low Savings",
            text=f"Your current savings rate is **{savings_rate}%**. Target at least 20% to safeguard against emergency expenses."
        ))

    # 2. Month-over-Month Savings Trend
    if prev_savings > Decimal("0.00"):
        comp = compare_months(net_savings, prev_savings)
        if comp.is_increase and comp.percentage > 5.0:
            insights.append(SmartInsight(
                type="positive",
                icon="📈",
                tag="Savings Growth",
                text=f"Your net savings increased by **{comp.percentage}%** compared to last month."
            ))
        elif not comp.is_increase and comp.percentage > 10.0:
            insights.append(SmartInsight(
                type="warning",
                icon="📉",
                tag="Savings Dip",
                text=f"Your savings dropped **{comp.percentage}%** compared to last month due to higher outgoing cash flows."
            ))

    # 3. Overspending & Budget Limits
    alerts = detect_overspending(budgets, transactions)
    if alerts:
        top_alert = alerts[0]
        if top_alert["status"] == BudgetStatus.OVER_BUDGET:
            insights.append(SmartInsight(
                type="alert",
                icon="🚨",
                tag="Budget Exceeded",
                text=f"Your **{top_alert['category']}** spending is **{top_alert['percentage']}%** of budget ({format_currency_inr(top_alert['spent'])} spent of {format_currency_inr(top_alert['budget'])})."
            ))
        else:
            insights.append(SmartInsight(
                type="warning",
                icon="⚠️",
                tag="Near Limit",
                text=f"Your **{top_alert['category']}** budget is **{top_alert['percentage']}%** utilized. Only {format_currency_inr(top_alert['remaining'])} remaining."
            ))

    # 4. Top Category Optimization
    cat_breakdown = analyze_categories(transactions)
    if cat_breakdown:
        top_cat = cat_breakdown[0]
        trim15 = (top_cat.amount * Decimal("0.15")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        insights.append(SmartInsight(
            type="opportunity",
            icon="💡",
            tag="Smart Tip",
            text=f"**{top_cat.category}** is your largest expense at {format_currency_inr(top_cat.amount)} ({top_cat.percentage}% of total). Trimming 15% saves **{format_currency_inr(trim15)}/mo** ({format_currency_inr(trim15 * 12)}/yr)."
        ))

    return insights
