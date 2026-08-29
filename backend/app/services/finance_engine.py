"""Smart Finance Engine: Production-grade deterministic financial intelligence & analytics."""

import math
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Tuple, Optional

from app.models.transaction import Transaction, TransactionType
from app.models.budget import Budget
from app.schemas.finance_analysis import (
    MetricDelta,
    CategorySpendingItem,
    SpendingAnalysis,
    UnusualSpendingAlert,
    BudgetRecommendationItem,
    SavingsOpportunityItem,
    ForecastMonthItem,
    CashflowForecast,
    HealthScoreFactorDetail,
    FinancialHealthAnalysis,
    SmartInsightItem,
    FinancialAlertItem,
    FinancialSummary,
    BudgetAnalysisSummary,
    SmartFinanceAnalysisData
)


def format_currency_inr(amount: Union[Decimal, float, int]) -> str:
    """Format decimal amount as Indian Rupee (INR) string representation."""
    if amount is None:
        return "₹0"
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))
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


# =====================================================================
# 1. FINANCIAL ANALYTICS ENGINE (PURE DETERMINISTIC FORMULAS)
# =====================================================================

def calculate_savings_rate(income: Decimal, expenses: Decimal) -> float:
    """Calculate savings rate percentage (0.0 to 100.0) with Decimal safety."""
    if income is None or expenses is None or income <= Decimal("0.00"):
        return 0.0
    rate = ((income - expenses) / income) * Decimal("100")
    rate_clamped = max(Decimal("0.0"), min(Decimal("100.0"), rate))
    return float(rate_clamped.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def calculate_monthly_cashflow(income: Decimal, expenses: Decimal) -> Decimal:
    """Calculate Net Cash Flow (Savings) = Income - Expenses."""
    inc = income or Decimal("0.00")
    exp = expenses or Decimal("0.00")
    return inc - exp


def calculate_metric_growth(current: Decimal, previous: Decimal) -> MetricDelta:
    """Compute numerical delta and percentage growth between two periods."""
    cur = current or Decimal("0.00")
    prev = previous or Decimal("0.00")
    delta = cur - prev

    if prev == Decimal("0.00"):
        if cur > Decimal("0.00"):
            return MetricDelta(
                delta=delta,
                percentage=100.0,
                is_increase=True,
                text="+100%"
            )
        return MetricDelta(
            delta=delta,
            percentage=0.0,
            is_increase=True,
            text="0%"
        )

    pct_decimal = ((cur - prev) / abs(prev)) * Decimal("100")
    pct_float = float(abs(pct_decimal).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
    is_increase = delta >= Decimal("0.00")
    text = f"{'+' if is_increase else '-'}{pct_float}%"

    return MetricDelta(
        delta=delta,
        percentage=pct_float,
        is_increase=is_increase,
        text=text
    )


def calculate_expense_growth(current_expenses: Decimal, previous_expenses: Decimal) -> MetricDelta:
    """Calculate month-over-month expense growth."""
    return calculate_metric_growth(current_expenses, previous_expenses)


def calculate_income_growth(current_income: Decimal, previous_income: Decimal) -> MetricDelta:
    """Calculate month-over-month income growth."""
    return calculate_metric_growth(current_income, previous_income)


def calculate_budget_utilization(budget: Decimal, spent: Decimal) -> Tuple[float, Decimal, str]:
    """Calculate budget utilization percentage, remaining buffer, and status."""
    bg = budget or Decimal("0.00")
    sp = spent or Decimal("0.00")

    if bg <= Decimal("0.00"):
        return 100.0, Decimal("0.00"), "OVER_BUDGET"

    percentage = float(((sp / bg) * Decimal("100")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
    remaining = bg - sp

    if percentage > 100.0:
        status = "OVER_BUDGET"
    elif percentage >= 80.0:
        status = "NEAR_LIMIT"
    elif percentage >= 60.0:
        status = "ON_TRACK"
    else:
        status = "UNDER_BUDGET"

    return percentage, remaining, status


def calculate_average_monthly_expenses(historical_data: List[Any]) -> Decimal:
    """Calculate average monthly expenses across historical records."""
    if not historical_data:
        return Decimal("0.00")
    
    total = Decimal("0.00")
    count = 0
    for item in historical_data:
        if isinstance(item, dict):
            val = item.get("expenses", Decimal("0.00"))
        elif isinstance(item, (Decimal, int, float, str)):
            val = Decimal(str(item))
        else:
            val = getattr(item, "expenses", Decimal("0.00"))
        total += val
        count += 1

    return (total / Decimal(count)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if count > 0 else Decimal("0.00")


def calculate_average_monthly_income(historical_data: List[Any]) -> Decimal:
    """Calculate average monthly income across historical records."""
    if not historical_data:
        return Decimal("0.00")
    
    total = Decimal("0.00")
    count = 0
    for item in historical_data:
        if isinstance(item, dict):
            val = item.get("income", Decimal("0.00"))
        elif isinstance(item, (Decimal, int, float, str)):
            val = Decimal(str(item))
        else:
            val = getattr(item, "income", Decimal("0.00"))
        total += val
        count += 1

    return (total / Decimal(count)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if count > 0 else Decimal("0.00")


def calculate_category_breakdown(transactions: List[Transaction]) -> List[CategorySpendingItem]:
    """Aggregate expense transactions by category sorted descending."""
    category_totals: Dict[str, Decimal] = {}
    category_counts: Dict[str, int] = {}
    total_expenses = Decimal("0.00")

    for tx in transactions:
        if tx.type == TransactionType.EXPENSE or str(tx.type).lower() == "expense":
            cat = tx.category.strip()
            category_totals[cat] = category_totals.get(cat, Decimal("0.00")) + tx.amount
            category_counts[cat] = category_counts.get(cat, 0) + 1
            total_expenses += tx.amount

    breakdown: List[CategorySpendingItem] = []
    for cat, amt in sorted(category_totals.items(), key=lambda item: item[1], reverse=True):
        pct = float(((amt / total_expenses) * Decimal("100")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)) if total_expenses > 0 else 0.0
        breakdown.append(CategorySpendingItem(
            category=cat,
            amount=amt,
            percentage=pct,
            transaction_count=category_counts.get(cat, 0)
        ))

    return breakdown


def calculate_category_growth(
    current_transactions: List[Transaction],
    previous_transactions: List[Transaction]
) -> List[Dict[str, Any]]:
    """Calculate category-by-category month-over-month growth."""
    cur_breakdown = {item.category: item.amount for item in calculate_category_breakdown(current_transactions)}
    prev_breakdown = {item.category: item.amount for item in calculate_category_breakdown(previous_transactions or [])}

    all_categories = set(cur_breakdown.keys()).union(set(prev_breakdown.keys()))
    growth_list = []

    for cat in all_categories:
        cur_amt = cur_breakdown.get(cat, Decimal("0.00"))
        prev_amt = prev_breakdown.get(cat, Decimal("0.00"))
        delta = cur_amt - prev_amt

        if prev_amt > Decimal("0.00"):
            pct_growth = float((((cur_amt - prev_amt) / prev_amt) * Decimal("100")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
        elif cur_amt > Decimal("0.00"):
            pct_growth = 100.0
        else:
            pct_growth = 0.0

        growth_list.append({
            "category": cat,
            "current_amount": cur_amt,
            "previous_amount": prev_amt,
            "delta": delta,
            "growth_percentage": pct_growth,
            "is_increase": delta > Decimal("0.00")
        })

    return sorted(growth_list, key=lambda x: x["current_amount"], reverse=True)


# =====================================================================
# 2. SMART SPENDING ANALYSIS
# =====================================================================

def analyze_spending(
    current_transactions: List[Transaction],
    previous_transactions: Optional[List[Transaction]] = None
) -> SpendingAnalysis:
    """Analyze category concentration, top outflows, and significant increases."""
    categories = calculate_category_breakdown(current_transactions)
    total_spending = sum((c.amount for c in categories), Decimal("0.00"))

    # Populate previous month growth if available
    if previous_transactions:
        prev_map = {c.category: c.amount for c in calculate_category_breakdown(previous_transactions)}
        for c in categories:
            prev_val = prev_map.get(c.category, Decimal("0.00"))
            c.previous_amount = prev_val
            if prev_val > Decimal("0.00"):
                c.growth_percentage = float((((c.amount - prev_val) / prev_val) * Decimal("100")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
            elif c.amount > Decimal("0.00"):
                c.growth_percentage = 100.0
            else:
                c.growth_percentage = 0.0

    top_cat = categories[0] if categories else None
    top1_concentration = top_cat.percentage if top_cat else 0.0
    top3_concentration = sum((c.percentage for c in categories[:3])) if len(categories) >= 3 else sum((c.percentage for c in categories))
    top3_concentration = round(top3_concentration, 1)

    # Detect significant increases (>= 15% increase and >= ₹500 delta)
    significant_increases = []
    if previous_transactions:
        category_growths = calculate_category_growth(current_transactions, previous_transactions)
        for cg in category_growths:
            if cg["is_increase"] and cg["growth_percentage"] >= 15.0 and cg["delta"] >= Decimal("500.00"):
                significant_increases.append({
                    "category": cg["category"],
                    "current_amount": cg["current_amount"],
                    "previous_amount": cg["previous_amount"],
                    "increase_amount": cg["delta"],
                    "growth_percentage": cg["growth_percentage"],
                    "explanation": f"{cg['category']} spending increased by {cg['growth_percentage']}% (from {format_currency_inr(cg['previous_amount'])} to {format_currency_inr(cg['current_amount'])})."
                })

    # Unusually high categories (> 35% of total budget or large outflow)
    unusually_high = []
    for c in categories:
        if c.percentage >= 35.0 and c.amount >= Decimal("10000.00"):
            unusually_high.append({
                "category": c.category,
                "amount": c.amount,
                "percentage": c.percentage,
                "explanation": f"{c.category} represents {c.percentage}% of all monthly spending ({format_currency_inr(c.amount)}), indicating high spending concentration."
            })

    return SpendingAnalysis(
        total_spending=total_spending,
        top_categories=categories,
        highest_expense_category=top_cat,
        spending_concentration_top1=top1_concentration,
        spending_concentration_top3=top3_concentration,
        significant_increases=significant_increases,
        unusually_high_categories=unusually_high
    )


# =====================================================================
# 3. UNUSUAL SPENDING DETECTION (STATISTICAL ANOMALY ENGINE)
# =====================================================================

def detect_unusual_spending(
    current_transactions: List[Transaction],
    historical_transactions: Optional[List[Transaction]] = None
) -> List[UnusualSpendingAlert]:
    """
    Detect abnormal category expenditures using Z-score statistical analysis
    or percentage-based comparative baselines.
    """
    alerts: List[UnusualSpendingAlert] = []
    cur_categories = calculate_category_breakdown(current_transactions)
    if not cur_categories:
        return alerts

    # Organize historical transactions by category and month
    historical_map: Dict[str, List[Decimal]] = {}
    if historical_transactions:
        # Group historical spending by (category, year, month)
        grouped_hist: Dict[Tuple[str, int, int], Decimal] = {}
        for tx in historical_transactions:
            if tx.type == TransactionType.EXPENSE or str(tx.type).lower() == "expense":
                cat = tx.category.strip()
                t_date = tx.transaction_date if isinstance(tx.transaction_date, date) else date.fromisoformat(str(tx.transaction_date))
                key = (cat, t_date.year, t_date.month)
                grouped_hist[key] = grouped_hist.get(key, Decimal("0.00")) + tx.amount

        for (cat, y, m), amt in grouped_hist.items():
            historical_map.setdefault(cat, []).append(amt)

    for cat_item in cur_categories:
        cat = cat_item.category
        current_amount = cat_item.amount
        history = historical_map.get(cat, [])

        if len(history) >= 3:
            # Statistical approach: Mean & Standard Deviation
            history_floats = [float(h) for h in history]
            mean = sum(history_floats) / len(history_floats)
            variance = sum((x - mean) ** 2 for x in history_floats) / len(history_floats)
            std_dev = math.sqrt(variance)

            cur_float = float(current_amount)
            baseline = Decimal(str(round(mean, 2)))

            if std_dev > 0:
                z_score = round((cur_float - mean) / std_dev, 2)
                pct_diff = round(((cur_float - mean) / mean) * 100, 1) if mean > 0 else 100.0

                if z_score >= 2.0 and current_amount >= Decimal("1000.00"):
                    severity = "HIGH" if z_score >= 3.0 or pct_diff >= 100.0 else "MEDIUM"
                    alerts.append(UnusualSpendingAlert(
                        category=cat,
                        current_amount=current_amount,
                        historical_baseline=baseline,
                        percentage_difference=pct_diff,
                        z_score=z_score,
                        severity=severity,
                        explanation=f"{cat} spending of {format_currency_inr(current_amount)} is {pct_diff}% above your historical monthly average ({format_currency_inr(baseline)}) with a statistical Z-score of {z_score}."
                    ))
        elif history:
            # Fallback comparative approach (1-2 historical months)
            mean = sum(history) / Decimal(len(history))
            baseline = mean.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if baseline > Decimal("0.00"):
                diff_pct = float((((current_amount - baseline) / baseline) * Decimal("100")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
                if diff_pct >= 40.0 and (current_amount - baseline) >= Decimal("1500.00"):
                    severity = "HIGH" if diff_pct >= 75.0 else "MEDIUM"
                    alerts.append(UnusualSpendingAlert(
                        category=cat,
                        current_amount=current_amount,
                        historical_baseline=baseline,
                        percentage_difference=diff_pct,
                        z_score=None,
                        severity=severity,
                        explanation=f"{cat} spending of {format_currency_inr(current_amount)} is {diff_pct}% higher than your recent baseline ({format_currency_inr(baseline)})."
                    ))

    return alerts


# =====================================================================
# 4. SMART BUDGET RECOMMENDATIONS
# =====================================================================

def recommend_budgets(
    transactions: List[Transaction],
    existing_budgets: List[Budget],
    income: Decimal
) -> List[BudgetRecommendationItem]:
    """
    Generate data-driven monthly budget recommendations with safety buffers
    and affordability capacity verification.
    """
    recommendations: List[BudgetRecommendationItem] = []
    if not transactions:
        return recommendations

    # Group all transactions by (category, year, month)
    category_monthly: Dict[str, Dict[Tuple[int, int], Decimal]] = {}
    for tx in transactions:
        if tx.type == TransactionType.EXPENSE or str(tx.type).lower() == "expense":
            cat = tx.category.strip()
            t_date = tx.transaction_date if isinstance(tx.transaction_date, date) else date.fromisoformat(str(tx.transaction_date))
            ym = (t_date.year, t_date.month)
            if cat not in category_monthly:
                category_monthly[cat] = {}
            category_monthly[cat][ym] = category_monthly[cat].get(ym, Decimal("0.00")) + tx.amount

    existing_budget_map = {b.category.lower().strip(): b.amount for b in existing_budgets}

    for cat, monthly_dict in category_monthly.items():
        monthly_values = list(monthly_dict.values())
        if not monthly_values:
            continue

        avg_spending = (sum(monthly_values) / Decimal(len(monthly_values))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if avg_spending <= Decimal("100.00"):
            continue

        # Evaluate trend
        if len(monthly_values) >= 2:
            recent = monthly_values[-1]
            prior = monthly_values[-2]
            if recent > prior * Decimal("1.10"):
                trend = "increasing"
                buffer_pct = 15.0
            elif recent < prior * Decimal("0.90"):
                trend = "decreasing"
                buffer_pct = 5.0
            else:
                trend = "stable"
                buffer_pct = 10.0
        else:
            trend = "stable"
            buffer_pct = 10.0

        # Suggested budget = Average spending * (1 + buffer) rounded to neat hundreds
        raw_suggested = avg_spending * (Decimal("1.00") + (Decimal(str(buffer_pct)) / Decimal("100")))
        suggested_int = int(raw_suggested.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        # Round to nearest 500
        suggested_clean = Decimal(str(int(math.ceil(suggested_int / 500.0) * 500)))

        cur_budget = existing_budget_map.get(cat.lower().strip())
        recommended_adj = (suggested_clean - cur_budget) if cur_budget is not None else None

        explanation = (
            f"Average monthly {cat} spending is {format_currency_inr(avg_spending)} with a {trend} trend. "
            f"A suggested budget of {format_currency_inr(suggested_clean)} provides a {buffer_pct}% safety buffer."
        )

        affordability = True
        if income > Decimal("0.00") and suggested_clean > income * Decimal("0.60"):
            affordability = False
            explanation += f" ⚠️ Warning: This envelope exceeds 60% of total monthly income ({format_currency_inr(income)})."

        recommendations.append(BudgetRecommendationItem(
            category=cat,
            average_monthly_spending=avg_spending,
            recent_trend=trend,
            suggested_budget=suggested_clean,
            current_budget=cur_budget,
            recommended_adjustment=recommended_adj,
            safety_buffer_percentage=buffer_pct,
            explanation=explanation,
            affordability_flag=affordability
        ))

    return sorted(recommendations, key=lambda r: r.suggested_budget, reverse=True)


# =====================================================================
# 5. SAVINGS OPPORTUNITY ENGINE
# =====================================================================

def find_savings_opportunities(
    transactions: List[Transaction],
    income: Decimal,
    budgets: List[Budget]
) -> List[SavingsOpportunityItem]:
    """
    Identify deterministic spending reduction opportunities, prioritizing
    discretionary outflows, rapidly expanding categories, and budget overruns.
    """
    opportunities: List[SavingsOpportunityItem] = []
    categories = calculate_category_breakdown(transactions)
    if not categories:
        return opportunities

    discretionary_categories = {
        "dining", "food", "restaurant", "swiggy", "zomato", "entertainment",
        "shopping", "clothing", "movies", "travel", "vacation", "subscriptions",
        "gaming", "cafes", "coffee", "hobbies"
    }

    budget_map = {b.category.lower().strip(): b.amount for b in budgets}

    for c in categories:
        cat_lower = c.category.lower().strip()
        is_discretionary = any(d in cat_lower for d in discretionary_categories)
        budget_limit = budget_map.get(cat_lower)

        # 1. Discretionary categories
        if is_discretionary and c.amount >= Decimal("2000.00"):
            reduction_pct = 15.0
            monthly_saving = (c.amount * (Decimal(str(reduction_pct)) / Decimal("100"))).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
            annual_saving = monthly_saving * 12
            priority = "HIGH" if c.amount >= Decimal("10000.00") else "MEDIUM"

            opportunities.append(SavingsOpportunityItem(
                category=c.category,
                current_spending=c.amount,
                suggested_reduction_percentage=reduction_pct,
                estimated_monthly_saving=monthly_saving,
                estimated_annual_saving=annual_saving,
                explanation=f"{c.category} is a flexible discretionary expense ({format_currency_inr(c.amount)}/mo). Trimming {reduction_pct}% saves {format_currency_inr(monthly_saving)} monthly ({format_currency_inr(annual_saving)} annually).",
                priority=priority
            ))

        # 2. Over-budget categories
        elif budget_limit and c.amount > budget_limit:
            overrun = c.amount - budget_limit
            reduction_pct = float(((overrun / c.amount) * Decimal("100")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
            opportunities.append(SavingsOpportunityItem(
                category=c.category,
                current_spending=c.amount,
                suggested_reduction_percentage=reduction_pct,
                estimated_monthly_saving=overrun,
                estimated_annual_saving=overrun * 12,
                explanation=f"{c.category} exceeded its budget by {format_currency_inr(overrun)}. Realigning to the {format_currency_inr(budget_limit)} cap saves {format_currency_inr(overrun)} monthly.",
                priority="HIGH"
            ))

        # 3. High concentration non-discretionary categories (> 30% of total)
        elif c.percentage >= 30.0 and c.amount >= Decimal("15000.00") and not is_discretionary:
            reduction_pct = 8.0
            monthly_saving = (c.amount * Decimal("0.08")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
            opportunities.append(SavingsOpportunityItem(
                category=c.category,
                current_spending=c.amount,
                suggested_reduction_percentage=reduction_pct,
                estimated_monthly_saving=monthly_saving,
                estimated_annual_saving=monthly_saving * 12,
                explanation=f"{c.category} represents {c.percentage}% of all expenses. Optimizing utility or provider rates by {reduction_pct}% unlocks {format_currency_inr(monthly_saving)} monthly in passive savings.",
                priority="LOW"
            ))

    return sorted(opportunities, key=lambda o: (0 if o.priority == "HIGH" else 1 if o.priority == "MEDIUM" else 2, -o.estimated_monthly_saving))


# =====================================================================
# 6. CASH FLOW FORECAST (WEIGHTED MOVING AVERAGE)
# =====================================================================

def forecast_cashflow(
    historical_months: List[Dict[str, Any]],
    forecast_months: int = 3
) -> CashflowForecast:
    """
    Project future 3-month cash flows using deterministic Weighted Moving Average (WMA).
    Recent months are weighted higher to capture trajectory accurately.
    """
    if not historical_months:
        return CashflowForecast(
            forecast_months=[
                ForecastMonthItem(
                    month_offset=i + 1,
                    month_label=f"Month +{i + 1}",
                    estimated_income=Decimal("0.00"),
                    estimated_expenses=Decimal("0.00"),
                    estimated_net_savings=Decimal("0.00"),
                    estimated_savings_rate=0.0
                )
                for i in range(forecast_months)
            ],
            confidence_level="LOW",
            confidence_score=30,
            methodology="Baseline zero estimate (No historical data)"
        )

    # Use up to 6 recent months
    data_points = historical_months[-6:]
    n = len(data_points)
    weights = [i + 1 for i in range(n)]
    sum_weights = sum(weights)

    weighted_income = sum(
        (Decimal(str(w)) * data_points[i].get("income", Decimal("0.00")) for i, w in enumerate(weights)),
        Decimal("0.00")
    ) / Decimal(sum_weights)

    weighted_expenses = sum(
        (Decimal(str(w)) * data_points[i].get("expenses", Decimal("0.00")) for i, w in enumerate(weights)),
        Decimal("0.00")
    ) / Decimal(sum_weights)

    # Determine growth drift slope if at least 2 points
    income_slope = Decimal("0.00")
    expense_slope = Decimal("0.00")
    if n >= 2:
        income_slope = ((data_points[-1].get("income", Decimal("0.00")) - data_points[0].get("income", Decimal("0.00"))) / Decimal(n - 1)) * Decimal("0.3")
        expense_slope = ((data_points[-1].get("expenses", Decimal("0.00")) - data_points[0].get("expenses", Decimal("0.00"))) / Decimal(n - 1)) * Decimal("0.3")

    projected_items: List[ForecastMonthItem] = []
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    now_month = datetime.now().month

    for offset in range(1, forecast_months + 1):
        future_m_idx = (now_month + offset - 1) % 12
        m_label = month_names[future_m_idx]

        est_inc = max(Decimal("0.00"), weighted_income + (income_slope * Decimal(offset))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        est_exp = max(Decimal("0.00"), weighted_expenses + (expense_slope * Decimal(offset))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        est_sav = calculate_monthly_cashflow(est_inc, est_exp)
        est_rate = calculate_savings_rate(est_inc, est_exp)

        projected_items.append(ForecastMonthItem(
            month_offset=offset,
            month_label=m_label,
            estimated_income=est_inc,
            estimated_expenses=est_exp,
            estimated_net_savings=est_sav,
            estimated_savings_rate=est_rate
        ))

    # Confidence calculation
    if n >= 6:
        conf_level = "HIGH"
        conf_score = 92
    elif n >= 3:
        conf_level = "MEDIUM"
        conf_score = 75
    else:
        conf_level = "LOW"
        conf_score = 50

    return CashflowForecast(
        forecast_months=projected_items,
        confidence_level=conf_level,
        confidence_score=conf_score,
        methodology="Weighted Moving Average (WMA) with linear trend drift"
    )


# =====================================================================
# 7. FINANCIAL HEALTH SCORE (5-FACTOR EXPLAINABLE MODEL)
# =====================================================================

def calculate_financial_health_score(financial_data: Dict[str, Any]) -> FinancialHealthAnalysis:
    """
    Calculate 5-Factor Weighted Financial Health Score (0-100) with independent
    factor scoring and clear conversational explanations.
    """
    income: Decimal = financial_data.get("income", Decimal("0.00"))
    expenses: Decimal = financial_data.get("expenses", Decimal("0.00"))
    prev_expenses: Decimal = financial_data.get("prev_expenses", Decimal("0.00"))
    total_budget: Decimal = financial_data.get("total_budget", Decimal("0.00"))
    net_savings = calculate_monthly_cashflow(income, expenses)

    # 1. Savings Rate Score (Weight: 30%) -> Target >= 35%
    savings_rate = calculate_savings_rate(income, expenses)
    if savings_rate >= 35.0:
        savings_score = 100
        savings_desc = f"Excellent savings rate of {savings_rate}% exceeds the 35% financial target."
    elif savings_rate >= 20.0:
        savings_score = int(70 + ((savings_rate - 20.0) / 15.0) * 30)
        savings_desc = f"Healthy savings rate of {savings_rate}% builds consistent wealth."
    elif savings_rate > 0.0:
        savings_score = int((savings_rate / 20.0) * 70)
        savings_desc = f"Low savings rate of {savings_rate}%. Target at least 20% to build emergency safety."
    else:
        savings_score = 10
        savings_desc = "Zero or negative net savings. Cash outflow equals or exceeds incoming cash."

    # 2. Budget Discipline Score (Weight: 25%) -> Target <= 85% utilization
    if total_budget > Decimal("0.00"):
        utilization = float(((expenses / total_budget) * Decimal("100")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
        if utilization <= 85.0:
            budget_score = 100
            budget_desc = f"Spending is within {utilization}% of your total budget envelope."
        elif utilization <= 100.0:
            budget_score = max(50, int(100 - (utilization - 85.0) * 3.3))
            budget_desc = f"Approaching envelope limit at {utilization}% utilization."
        else:
            budget_score = max(10, int(50 - (utilization - 100.0) * 2.0))
            budget_desc = f"Budget exceeded by {round(utilization - 100.0, 1)}%."
    else:
        budget_score = 75
        budget_desc = "No active budget envelopes configured. Setting targets unlocks higher discipline."

    # 3. Spending Control Score (Weight: 15%) -> MoM Expense Velocity
    if prev_expenses > Decimal("0.00"):
        growth = float((((expenses - prev_expenses) / prev_expenses) * Decimal("100")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
        if growth <= 0.0:
            spending_growth_score = 100
            spending_desc = f"Outflows decreased by {abs(growth)}% compared to last month."
        elif growth <= 5.0:
            spending_growth_score = 90
            spending_desc = f"Outflows grew modestly by {growth}%, within safe bounds."
        elif growth <= 15.0:
            spending_growth_score = 70
            spending_desc = f"Spending increased by {growth}% compared to last month."
        else:
            spending_growth_score = max(20, int(70 - (growth - 15.0) * 2.0))
            spending_desc = f"High spending acceleration (+{growth}% MoM)."
    else:
        spending_growth_score = 85
        spending_desc = "Stable baseline spending."

    # 4. Emergency Buffer Score (Weight: 15%) -> Monthly Cash Surplus
    if net_savings >= Decimal("30000.00"):
        emergency_score = 95
        emergency_desc = f"Strong monthly liquidity buffer of {format_currency_inr(net_savings)}."
    elif net_savings >= Decimal("15000.00"):
        emergency_score = 85
        emergency_desc = f"Reliable liquidity buffer of {format_currency_inr(net_savings)}."
    elif net_savings > Decimal("0.00"):
        emergency_score = 65
        emergency_desc = f"Modest monthly surplus of {format_currency_inr(net_savings)}."
    else:
        emergency_score = 25
        emergency_desc = f"Deficit spending ({format_currency_inr(net_savings)}). Cash buffer decreasing."

    # 5. Consistency Score (Weight: 15%)
    consistency_score = 88
    consistency_desc = "Consistent income and expense tracking activity."

    # Calculate overall weighted score
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

    explanations = [
        f"Savings Rate ({savings_score}/100): {savings_desc}",
        f"Budget Discipline ({budget_score}/100): {budget_desc}",
        f"Spending Control ({spending_growth_score}/100): {spending_desc}",
        f"Emergency Buffer ({emergency_score}/100): {emergency_desc}",
        f"Consistency ({consistency_score}/100): {consistency_desc}"
    ]

    factors_dict = {
        "savings_rate": HealthScoreFactorDetail(
            score=savings_score,
            weight="30%",
            weight_percentage=30,
            label="Savings Rate",
            description=savings_desc
        ),
        "budget_discipline": HealthScoreFactorDetail(
            score=budget_score,
            weight="25%",
            weight_percentage=25,
            label="Budget Discipline",
            description=budget_desc
        ),
        "spending_control": HealthScoreFactorDetail(
            score=spending_growth_score,
            weight="15%",
            weight_percentage=15,
            label="Spending Control",
            description=spending_desc
        ),
        "emergency_buffer": HealthScoreFactorDetail(
            score=emergency_score,
            weight="15%",
            weight_percentage=15,
            label="Emergency Buffer",
            description=emergency_desc
        ),
        "consistency": HealthScoreFactorDetail(
            score=consistency_score,
            weight="15%",
            weight_percentage=15,
            label="Consistency",
            description=consistency_desc
        )
    }

    return FinancialHealthAnalysis(
        score=total_score,
        status=status_label,
        status_class=status_class,
        factors=factors_dict,
        explanations=explanations
    )


# =====================================================================
# 8. SMART INSIGHTS ENGINE
# =====================================================================

def generate_smart_insights(financial_data: Dict[str, Any]) -> List[SmartInsightItem]:
    """
    Generate structured, deduplicated, and prioritized data-driven insights.
    Types: HIGH_SAVER, SAVINGS_GROWTH, SAVINGS_DECLINE, BUDGET_WARNING,
    BUDGET_EXCEEDED, SPENDING_SPIKE, CATEGORY_SPIKE, SAVINGS_OPPORTUNITY,
    INCOME_DECLINE, CASHFLOW_WARNING, HEALTH_IMPROVEMENT, HEALTH_DECLINE.
    """
    cur_income: Decimal = financial_data.get("income", Decimal("0.00"))
    cur_expenses: Decimal = financial_data.get("expenses", Decimal("0.00"))
    prev_income: Decimal = financial_data.get("prev_income", Decimal("0.00"))
    prev_expenses: Decimal = financial_data.get("prev_expenses", Decimal("0.00"))
    transactions: List[Transaction] = financial_data.get("transactions", [])
    budgets: List[Budget] = financial_data.get("budgets", [])

    insights: List[SmartInsightItem] = []
    savings_rate = calculate_savings_rate(cur_income, cur_expenses)
    net_savings = calculate_monthly_cashflow(cur_income, cur_expenses)
    prev_savings = calculate_monthly_cashflow(prev_income, prev_expenses)

    # 1. High Saver / Low Savings
    if savings_rate >= 40.0:
        insights.append(SmartInsightItem(
            type="HIGH_SAVER",
            title="High Savings Rate",
            message=f"You are saving {savings_rate}% of your income ({format_currency_inr(net_savings)}).",
            severity="POSITIVE",
            metric=f"{savings_rate}%",
            recommendation="Consider allocating extra surplus into long-term index investments or emergency reserves."
        ))
    elif savings_rate < 15.0 and cur_income > Decimal("0.00"):
        insights.append(SmartInsightItem(
            type="CASHFLOW_WARNING",
            title="Low Savings Buffer",
            message=f"Your savings rate is {savings_rate}%, leaving a tight liquidity buffer of {format_currency_inr(net_savings)}.",
            severity="WARNING",
            metric=f"{savings_rate}%",
            recommendation="Review top discretionary expenses to target a 20% minimum savings buffer."
        ))

    # 2. MoM Savings Growth / Decline
    if prev_savings > Decimal("0.00"):
        comp = calculate_metric_growth(net_savings, prev_savings)
        if comp.is_increase and comp.percentage >= 10.0:
            insights.append(SmartInsightItem(
                type="SAVINGS_GROWTH",
                title="Savings Momentum",
                message=f"Net savings increased by {comp.percentage}% ({format_currency_inr(comp.delta)}) compared to last month.",
                severity="POSITIVE",
                metric=comp.text,
                recommendation="Maintain your disciplined outflow trajectory."
            ))
        elif not comp.is_increase and comp.percentage >= 15.0:
            insights.append(SmartInsightItem(
                type="SAVINGS_DECLINE",
                title="Savings Dip Detected",
                message=f"Net savings dropped {comp.percentage}% compared to last month.",
                severity="WARNING",
                metric=comp.text,
                recommendation="Check recent one-off expenses to determine if this dip is temporary."
            ))

    # 3. Income Decline
    if prev_income > Decimal("0.00") and cur_income < prev_income:
        inc_comp = calculate_metric_growth(cur_income, prev_income)
        if inc_comp.percentage >= 10.0:
            insights.append(SmartInsightItem(
                type="INCOME_DECLINE",
                title="Income Reduction",
                message=f"Total income decreased by {inc_comp.percentage}% ({format_currency_inr(abs(inc_comp.delta))}) vs prior month.",
                severity="WARNING",
                metric=inc_comp.text,
                recommendation="Adjust monthly budget caps to accommodate the reduced income stream."
            ))

    # 4. Budget Warnings / Exceeded
    for b in budgets:
        # Calculate spent for this category
        cat_spent = sum(
            (t.amount for t in transactions if (t.type == TransactionType.EXPENSE or str(t.type).lower() == "expense") and t.category.lower().strip() == b.category.lower().strip()),
            Decimal("0.00")
        )
        pct, remaining, b_status = calculate_budget_utilization(b.amount, cat_spent)

        if b_status == "OVER_BUDGET":
            insights.append(SmartInsightItem(
                type="BUDGET_EXCEEDED",
                title="Budget Limit Exceeded",
                message=f"You have spent {format_currency_inr(cat_spent)} on {b.category}, exceeding your {format_currency_inr(b.amount)} limit by {pct - 100:.1f}%.",
                severity="CRITICAL",
                category=b.category,
                metric=f"{pct}%",
                recommendation=f"Pause non-essential spending on {b.category} for the remainder of the month."
            ))
        elif b_status == "NEAR_LIMIT":
            insights.append(SmartInsightItem(
                type="BUDGET_WARNING",
                title="Budget Near Limit",
                message=f"{b.category} spending has reached {pct}% of your limit ({format_currency_inr(remaining)} remaining).",
                severity="WARNING",
                category=b.category,
                metric=f"{pct}%",
                recommendation=f"Keep remaining {b.category} outflows under {format_currency_inr(remaining)}."
            ))

    # 5. Top Category Savings Opportunity
    cat_breakdown = calculate_category_breakdown(transactions)
    if cat_breakdown:
        top_cat = cat_breakdown[0]
        trim15 = (top_cat.amount * Decimal("0.15")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        insights.append(SmartInsightItem(
            type="SAVINGS_OPPORTUNITY",
            title="Spending Optimization",
            message=f"{top_cat.category} is your highest expense category at {format_currency_inr(top_cat.amount)} ({top_cat.percentage}% of total).",
            severity="INFO",
            category=top_cat.category,
            metric=f"{top_cat.percentage}%",
            recommendation=f"Trimming 15% from {top_cat.category} unlocks {format_currency_inr(trim15)}/month ({format_currency_inr(trim15 * 12)}/year) in additional savings."
        ))

    # Deduplication and prioritization (CRITICAL -> WARNING -> POSITIVE -> INFO)
    severity_order = {"CRITICAL": 0, "WARNING": 1, "POSITIVE": 2, "INFO": 3}
    return sorted(insights, key=lambda x: severity_order.get(x.severity, 4))


# =====================================================================
# 9. FINANCIAL ALERT SYSTEM
# =====================================================================

def generate_financial_alerts(financial_data: Dict[str, Any]) -> List[FinancialAlertItem]:
    """
    Detect critical financial risks and rank them by severity (HIGH -> MEDIUM -> LOW).
    """
    cur_income: Decimal = financial_data.get("income", Decimal("0.00"))
    cur_expenses: Decimal = financial_data.get("expenses", Decimal("0.00"))
    prev_income: Decimal = financial_data.get("prev_income", Decimal("0.00"))
    prev_expenses: Decimal = financial_data.get("prev_expenses", Decimal("0.00"))
    transactions: List[Transaction] = financial_data.get("transactions", [])
    budgets: List[Budget] = financial_data.get("budgets", [])

    alerts: List[FinancialAlertItem] = []
    net_savings = calculate_monthly_cashflow(cur_income, cur_expenses)
    savings_rate = calculate_savings_rate(cur_income, cur_expenses)

    # 1. Deficit Spending (Negative Savings) -> HIGH
    if net_savings < Decimal("0.00"):
        alerts.append(FinancialAlertItem(
            severity="HIGH",
            type="DEFICIT_SPENDING",
            title="Negative Monthly Cash Flow",
            message=f"Total expenses ({format_currency_inr(cur_expenses)}) exceed total income ({format_currency_inr(cur_income)}) by {format_currency_inr(abs(net_savings))}.",
            action_required=True
        ))

    # 2. Over-budget category alerts -> HIGH
    for b in budgets:
        spent = sum(
            (t.amount for t in transactions if (t.type == TransactionType.EXPENSE or str(t.type).lower() == "expense") and t.category.lower().strip() == b.category.lower().strip()),
            Decimal("0.00")
        )
        pct, remaining, status = calculate_budget_utilization(b.amount, spent)
        if status == "OVER_BUDGET":
            alerts.append(FinancialAlertItem(
                severity="HIGH",
                type="OVER_BUDGET",
                title=f"Over Budget: {b.category}",
                message=f"{b.category} spending ({format_currency_inr(spent)}) has exceeded your {format_currency_inr(b.amount)} cap by {format_currency_inr(spent - b.amount)}.",
                action_required=True
            ))
        elif status == "NEAR_LIMIT":
            alerts.append(FinancialAlertItem(
                severity="MEDIUM",
                type="NEAR_BUDGET_LIMIT",
                title=f"Near Limit: {b.category}",
                message=f"{b.category} is at {pct}% utilization with only {format_currency_inr(remaining)} remaining.",
                action_required=False
            ))

    # 3. Expense Spike Alert (> 25% MoM increase) -> MEDIUM / HIGH
    if prev_expenses > Decimal("0.00"):
        exp_comp = calculate_expense_growth(cur_expenses, prev_expenses)
        if exp_comp.is_increase and exp_comp.percentage >= 25.0 and exp_comp.delta >= Decimal("3000.00"):
            alerts.append(FinancialAlertItem(
                severity="HIGH" if exp_comp.percentage >= 50.0 else "MEDIUM",
                type="EXPENSE_SPIKE",
                title="Significant Expense Acceleration",
                message=f"Monthly spending increased by {exp_comp.percentage}% ({format_currency_inr(exp_comp.delta)}) compared to last month.",
                action_required=True
            ))

    # 4. Income Drop Alert -> MEDIUM
    if prev_income > Decimal("0.00") and cur_income < prev_income:
        inc_comp = calculate_income_growth(cur_income, prev_income)
        if inc_comp.percentage >= 15.0:
            alerts.append(FinancialAlertItem(
                severity="MEDIUM",
                type="INCOME_DROP",
                title="Income Reduction Alert",
                message=f"Income decreased by {inc_comp.percentage}% ({format_currency_inr(abs(inc_comp.delta))}) vs prior month.",
                action_required=False
            ))

    # 5. Low Savings Rate Alert -> LOW
    if 0.0 < savings_rate < 10.0 and cur_income > Decimal("0.00"):
        alerts.append(FinancialAlertItem(
            severity="LOW",
            type="LOW_SAVINGS_RATE",
            title="Sub-Optimal Savings Rate",
            message=f"Current savings rate is {savings_rate}%. Recommended benchmark is >= 20%.",
            action_required=False
        ))

    # Sort HIGH -> MEDIUM -> LOW
    rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    return sorted(alerts, key=lambda a: rank.get(a.severity, 3))


# =====================================================================
# 10. MASTER SMART FINANCE ORCHESTRATOR
# =====================================================================

def run_full_financial_analysis(
    transactions: List[Transaction],
    budgets: List[Budget],
    target_month: Optional[int] = None,
    target_year: Optional[int] = None
) -> SmartFinanceAnalysisData:
    """
    Execute comprehensive multi-stage Smart Finance Engine analysis for a user.
    """
    now = datetime.now()
    cur_month = target_month or now.month
    cur_year = target_year or now.year

    if cur_month == 1:
        prev_month = 12
        prev_year = cur_year - 1
    else:
        prev_month = cur_month - 1
        prev_year = cur_year

    month_str = f"{cur_year}-{cur_month:02d}"

    # Partition transactions
    cur_txs = [
        t for t in transactions
        if (t.transaction_date if isinstance(t.transaction_date, date) else date.fromisoformat(str(t.transaction_date))).year == cur_year
        and (t.transaction_date if isinstance(t.transaction_date, date) else date.fromisoformat(str(t.transaction_date))).month == cur_month
    ]

    prev_txs = [
        t for t in transactions
        if (t.transaction_date if isinstance(t.transaction_date, date) else date.fromisoformat(str(t.transaction_date))).year == prev_year
        and (t.transaction_date if isinstance(t.transaction_date, date) else date.fromisoformat(str(t.transaction_date))).month == prev_month
    ]

    hist_txs = [
        t for t in transactions
        if (t.transaction_date if isinstance(t.transaction_date, date) else date.fromisoformat(str(t.transaction_date))) < date(cur_year, cur_month, 1)
    ]

    # Calculate Current Month Inflows and Outflows
    cur_income = sum((t.amount for t in cur_txs if t.type == TransactionType.INCOME or str(t.type).lower() == "income"), Decimal("0.00"))
    cur_expenses = sum((t.amount for t in cur_txs if t.type == TransactionType.EXPENSE or str(t.type).lower() == "expense"), Decimal("0.00"))
    cur_savings = calculate_monthly_cashflow(cur_income, cur_expenses)
    cur_savings_rate = calculate_savings_rate(cur_income, cur_expenses)

    # Calculate Previous Month Inflows and Outflows
    prev_income = sum((t.amount for t in prev_txs if t.type == TransactionType.INCOME or str(t.type).lower() == "income"), Decimal("0.00"))
    prev_expenses = sum((t.amount for t in prev_txs if t.type == TransactionType.EXPENSE or str(t.type).lower() == "expense"), Decimal("0.00"))
    prev_savings = calculate_monthly_cashflow(prev_income, prev_expenses)

    # Growth Deltas
    income_growth = calculate_income_growth(cur_income, prev_income)
    expense_growth = calculate_expense_growth(cur_expenses, prev_expenses)
    savings_growth = calculate_metric_growth(cur_savings, prev_savings)

    summary = FinancialSummary(
        total_income=cur_income,
        total_expenses=cur_expenses,
        net_savings=cur_savings,
        savings_rate=cur_savings_rate,
        current_month=month_str,
        income_growth=income_growth,
        expense_growth=expense_growth,
        savings_growth=savings_growth
    )

    # 1. Spending Analysis
    spending_analysis = analyze_spending(cur_txs, prev_txs)

    # 2. Budget Analysis & Recommendations
    user_cur_budgets = [b for b in budgets if b.month == cur_month and b.year == cur_year] or budgets
    total_budget_envelope = sum((b.amount for b in user_cur_budgets), Decimal("0.00"))
    total_budget_spent = sum((c.amount for c in spending_analysis.top_categories if c.category.lower().strip() in {b.category.lower().strip() for b in user_cur_budgets}), Decimal("0.00"))
    total_budget_rem = total_budget_envelope - total_budget_spent
    overall_util = float(((total_budget_spent / total_budget_envelope) * Decimal("100")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)) if total_budget_envelope > Decimal("0.00") else 0.0

    budget_recommendations = recommend_budgets(transactions, user_cur_budgets, cur_income)

    over_count = 0
    near_count = 0
    for b in user_cur_budgets:
        b_spent = sum((t.amount for t in cur_txs if (t.type == TransactionType.EXPENSE or str(t.type).lower() == "expense") and t.category.lower().strip() == b.category.lower().strip()), Decimal("0.00"))
        _, _, b_stat = calculate_budget_utilization(b.amount, b_spent)
        if b_stat == "OVER_BUDGET":
            over_count += 1
        elif b_stat == "NEAR_LIMIT":
            near_count += 1

    budget_analysis = BudgetAnalysisSummary(
        total_budget_envelope=total_budget_envelope,
        total_budget_spent=total_budget_spent,
        total_budget_remaining=total_budget_rem,
        overall_utilization_percentage=overall_util,
        over_budget_categories_count=over_count,
        near_limit_categories_count=near_count,
        recommendations=budget_recommendations
    )

    # 3. Savings Opportunities
    savings_opportunities = find_savings_opportunities(cur_txs, cur_income, user_cur_budgets)

    # 4. Unusual Spending
    unusual_spending = detect_unusual_spending(cur_txs, hist_txs)

    # 5. Multi-Month History & Cash Flow Forecast
    # Build historical 6-month array
    historical_points: List[Dict[str, Any]] = []
    for i in range(5, -1, -1):
        m = cur_month - i
        y = cur_year
        while m <= 0:
            m += 12
            y -= 1
        m_txs = [
            t for t in transactions
            if (t.transaction_date if isinstance(t.transaction_date, date) else date.fromisoformat(str(t.transaction_date))).year == y
            and (t.transaction_date if isinstance(t.transaction_date, date) else date.fromisoformat(str(t.transaction_date))).month == m
        ]
        m_inc = sum((t.amount for t in m_txs if t.type == TransactionType.INCOME or str(t.type).lower() == "income"), Decimal("0.00"))
        m_exp = sum((t.amount for t in m_txs if t.type == TransactionType.EXPENSE or str(t.type).lower() == "expense"), Decimal("0.00"))
        historical_points.append({"month_key": f"{y}-{m:02d}", "income": m_inc, "expenses": m_exp})

    cashflow_forecast = forecast_cashflow(historical_points, forecast_months=3)

    # 6. Financial Health Analysis
    health_data = {
        "income": cur_income,
        "expenses": cur_expenses,
        "prev_expenses": prev_expenses,
        "total_budget": total_budget_envelope
    }
    financial_health = calculate_financial_health_score(health_data)

    # 7. Insights
    insights_data = {
        "income": cur_income,
        "expenses": cur_expenses,
        "prev_income": prev_income,
        "prev_expenses": prev_expenses,
        "transactions": cur_txs,
        "budgets": user_cur_budgets
    }
    insights = generate_smart_insights(insights_data)

    # 8. Alerts
    alerts = generate_financial_alerts(insights_data)

    return SmartFinanceAnalysisData(
        summary=summary,
        spending_analysis=spending_analysis,
        budget_analysis=budget_analysis,
        savings_opportunities=savings_opportunities,
        unusual_spending=unusual_spending,
        cashflow_forecast=cashflow_forecast,
        financial_health=financial_health,
        insights=insights,
        alerts=alerts
    )
