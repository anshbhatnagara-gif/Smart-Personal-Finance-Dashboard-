"""AI Tool Definitions: Function calling declarations for LLMs (e.g. Google Gemini)."""

from typing import List, Dict, Any

# Tool function declarations in standardized JSON schema format
FINANCIAL_TOOL_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "name": "get_transactions",
        "description": "Retrieve a list of transactions for the authenticated user with optional filters for category, type, and date range.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "category": {
                    "type": "STRING",
                    "description": "Optional category filter (e.g., Food, Rent, Salary, Entertainment, Utilities, Travel, Shopping)"
                },
                "transaction_type": {
                    "type": "STRING",
                    "description": "Optional transaction type: 'income' or 'expense'"
                },
                "start_date": {
                    "type": "STRING",
                    "description": "Optional start date in YYYY-MM-DD format"
                },
                "end_date": {
                    "type": "STRING",
                    "description": "Optional end date in YYYY-MM-DD format"
                },
                "limit": {
                    "type": "INTEGER",
                    "description": "Maximum number of transactions to return (1-50, default 20)"
                }
            }
        }
    },
    {
        "name": "get_transaction_summary",
        "description": "Retrieve financial totals (total income, total expenses, net savings, savings rate) for a specific month and year.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "month": {
                    "type": "INTEGER",
                    "description": "Target month (1-12). Defaults to current month."
                },
                "year": {
                    "type": "INTEGER",
                    "description": "Target year (e.g., 2026). Defaults to current year."
                }
            }
        }
    },
    {
        "name": "get_budget_progress",
        "description": "Retrieve budget envelope statuses, spending utilization, remaining buffer, velocity, and overspending risk predictions.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "month": {
                    "type": "INTEGER",
                    "description": "Target month (1-12). Defaults to current month."
                },
                "year": {
                    "type": "INTEGER",
                    "description": "Target year (e.g., 2026). Defaults to current year."
                }
            }
        }
    },
    {
        "name": "get_dashboard",
        "description": "Retrieve the complete dashboard summary including KPIs, category breakdown, financial health score, and smart insights.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "month": {
                    "type": "INTEGER",
                    "description": "Target month (1-12). Defaults to current month."
                },
                "year": {
                    "type": "INTEGER",
                    "description": "Target year (e.g., 2026). Defaults to current year."
                }
            }
        }
    },
    {
        "name": "get_category_spending",
        "description": "Retrieve categorized spending breakdown showing totals, percentages of outflow, and Month-over-Month changes.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "month": {
                    "type": "INTEGER",
                    "description": "Target month (1-12). Defaults to current month."
                },
                "year": {
                    "type": "INTEGER",
                    "description": "Target year (e.g., 2026). Defaults to current year."
                }
            }
        }
    },
    {
        "name": "get_monthly_cashflow",
        "description": "Retrieve multi-month cashflow history and trends (income vs expense vs savings) across recent months.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "months": {
                    "type": "INTEGER",
                    "description": "Number of recent months to analyze (1-12, default 6)."
                }
            }
        }
    },
    {
        "name": "get_spending_analysis",
        "description": "Perform deep spending behavior analysis including Month-over-Month changes, high-value recurring categories, and transaction anomalies/outliers.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "month": {
                    "type": "INTEGER",
                    "description": "Target month (1-12). Defaults to current month."
                },
                "year": {
                    "type": "INTEGER",
                    "description": "Target year (e.g., 2026). Defaults to current year."
                }
            }
        }
    },
    {
        "name": "get_savings_opportunities",
        "description": "Identify actionable, calculated monthly savings opportunities from discretionary expenses and budget overruns with exact potential ₹ savings.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "get_financial_health",
        "description": "Retrieve the comprehensive 5-factor Financial Health Score (Savings Discipline, Budget Adherence, Expense Ratio, Buffer Health, Outflow Concentration) with detailed interpretations and recommendations.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "get_proactive_insights",
        "description": "Retrieve prioritized proactive financial insights, spending alerts, and progress indicators generated by the insight engine.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "month": {
                    "type": "INTEGER",
                    "description": "Optional target month (1-12)."
                },
                "year": {
                    "type": "INTEGER",
                    "description": "Optional target year (e.g. 2026)."
                }
            }
        }
    },
    {
        "name": "get_spending_alerts",
        "description": "Retrieve high-priority spending alerts including category spending spikes, budget overruns, and unusual transaction outliers.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "month": {
                    "type": "INTEGER",
                    "description": "Optional target month (1-12)."
                },
                "year": {
                    "type": "INTEGER",
                    "description": "Optional target year (e.g. 2026)."
                }
            }
        }
    },
    {
        "name": "get_financial_changes",
        "description": "Retrieve period-over-period financial health score changes, savings rate trends, and category expense shifts.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "month": {
                    "type": "INTEGER",
                    "description": "Optional target month (1-12)."
                },
                "year": {
                    "type": "INTEGER",
                    "description": "Optional target year (e.g. 2026)."
                }
            }
        }
    },
    {
        "name": "get_financial_goals",
        "description": "Retrieve active financial goals for the authenticated user with target amounts, current saved balances, target deadlines, categories, and progress status.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "get_goal_progress",
        "description": "Retrieve progress metrics, remaining amounts, and timeline status for a specific goal or all active goals.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "goal_id": {
                    "type": "INTEGER",
                    "description": "Optional specific goal ID. If omitted, returns progress for all active goals."
                }
            }
        }
    },
    {
        "name": "calculate_goal_plan",
        "description": "Calculate required monthly and weekly savings contributions, projected completion date, and pace gaps for a goal.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "goal_id": {
                    "type": "INTEGER",
                    "description": "Required goal ID to generate savings plan for."
                }
            },
            "required": ["goal_id"]
        }
    },
    {
        "name": "calculate_affordability",
        "description": "Evaluate whether a planned financial goal, purchase, or monthly savings commitment is affordable based on verified cashflow and discretionary spending.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "required_monthly_amount": {
                    "type": "NUMBER",
                    "description": "Required monthly savings or expense commitment in INR."
                },
                "goal_id": {
                    "type": "INTEGER",
                    "description": "Optional goal ID to evaluate affordability for."
                }
            }
        }
    },
    {
        "name": "run_financial_scenario",
        "description": "Run deterministic 'What-If' scenario simulations (increased_savings, reduced_spending, increased_expenses, income_reduction, goal_deadline_change, monthly_contribution_change).",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "scenario_type": {
                    "type": "STRING",
                    "description": "Scenario type: 'increased_savings', 'reduced_spending', 'increased_expenses', 'income_reduction', 'goal_deadline_change', 'monthly_contribution_change'."
                },
                "goal_id": {
                    "type": "INTEGER",
                    "description": "Optional goal ID to apply the scenario to."
                },
                "amount": {
                    "type": "NUMBER",
                    "description": "Optional monetary amount parameter for the scenario in INR."
                },
                "percentage": {
                    "type": "NUMBER",
                    "description": "Optional percentage parameter for the scenario (e.g. 10.0 for 10%)."
                },
                "category": {
                    "type": "STRING",
                    "description": "Optional expense category for spending reduction/increase scenarios."
                },
                "months_delta": {
                    "type": "INTEGER",
                    "description": "Optional months to extend/shorten deadline for deadline scenarios."
                }
            },
            "required": ["scenario_type"]
        }
    },
    {
        "name": "get_coaching_context",
        "description": "Retrieve comprehensive financial coaching context synthesizing cashflow, active goals, largest expenses, discretionary ratios, proactive alerts, and financial health score.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "month": {
                    "type": "INTEGER",
                    "description": "Optional month (1-12)."
                },
                "year": {
                    "type": "INTEGER",
                    "description": "Optional year (e.g. 2026)."
                }
            }
        }
    },
    {
        "name": "get_financial_forecast",
        "description": "Retrieve comprehensive next-month financial forecast including income, expense breakdown, net savings, budget exhaustion pace, and goal timelines.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "get_cashflow_forecast",
        "description": "Retrieve next-month cashflow outlook, trend rates, and 6-month projected balance trajectory.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "get_expense_forecast",
        "description": "Retrieve projected next-month total expenses with category-level breakdowns and trend percentages.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "get_income_forecast",
        "description": "Retrieve verified next-month projected income, confidence level, and income stability trend.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "get_savings_forecast",
        "description": "Retrieve projected next-month net savings, projected savings rate percentage, and 6-month cumulative surplus trajectory.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "get_financial_risks",
        "description": "Evaluate and retrieve 10 deterministic financial risk signals (cashflow, savings, budget, goal delays, expense growth, debt pressure) with overall stress scoring.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "get_predictive_insights",
        "description": "Retrieve top prioritized predictive insights combining forecasts and risks with distinct labels for verified facts, forecasts, risks, and AI suggestions.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "get_forecast_explanation",
        "description": "Retrieve a detailed mathematical explanation, methodology, evidence, and limitations for financial projections.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "forecast_type": {
                    "type": "STRING",
                    "description": "Optional forecast type to explain: 'all', 'income', 'expense', 'savings', 'cashflow'."
                }
            }
        }
    },
    {
        "name": "get_smart_actions",
        "description": "Retrieve verified, active smart financial action recommendations (budget realignment, savings boost, goal acceleration, expense reduction) for the authenticated user.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "refresh": {
                    "type": "BOOLEAN",
                    "description": "Optional flag to force re-evaluation of candidate action recommendations."
                }
            }
        }
    },
    {
        "name": "get_action_details",
        "description": "Retrieve detailed parameters, verified evidence, expected impact, and status for a specific smart action proposal.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action_id": {
                    "type": "STRING",
                    "description": "Unique identifier of the smart action (e.g. 'act-a1b2c3d4')."
                }
            },
            "required": ["action_id"]
        }
    },
    {
        "name": "propose_financial_action",
        "description": "Create a new smart action proposal. Note: This creates a PROPOSED action only and does NOT execute any database modifications without explicit user confirmation.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action_type": {
                    "type": "STRING",
                    "description": "Type of action: BUDGET_ADJUSTMENT, SAVINGS_INCREASE, GOAL_CONTRIBUTION_ADJUSTMENT, EXPENSE_REDUCTION, RECURRING_EXPENSE_REVIEW, EMERGENCY_FUND_CONTRIBUTION, DEBT_PAYMENT_REVIEW, FINANCIAL_RISK_MITIGATION."
                },
                "title": {
                    "type": "STRING",
                    "description": "Short, clear title for the action proposal."
                },
                "description": {
                    "type": "STRING",
                    "description": "Detailed explanation of the proposed adjustment."
                },
                "financial_amount": {
                    "type": "NUMBER",
                    "description": "Relevant monetary amount in INR."
                }
            },
            "required": ["action_type", "title", "description"]
        }
    },
    {
        "name": "confirm_financial_action",
        "description": "Confirm an action proposal so it becomes eligible for server-side execution upon user approval.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action_id": {
                    "type": "STRING",
                    "description": "Unique action ID to confirm."
                },
                "note": {
                    "type": "STRING",
                    "description": "Optional confirmation note or rationale."
                }
            },
            "required": ["action_id"]
        }
    },
    {
        "name": "execute_financial_action",
        "description": "Safely execute a confirmed smart financial action on the server and record an immutable audit log. Requires prior confirmation.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action_id": {
                    "type": "STRING",
                    "description": "Unique action ID to execute."
                },
                "note": {
                    "type": "STRING",
                    "description": "Optional execution note."
                }
            },
            "required": ["action_id"]
        }
    },
    {
        "name": "reject_financial_action",
        "description": "Reject a smart action proposal and record the rejection reason in the audit trail.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action_id": {
                    "type": "STRING",
                    "description": "Unique action ID to reject."
                },
                "reason": {
                    "type": "STRING",
                    "description": "Optional reason for rejecting the action."
                }
            },
            "required": ["action_id"]
        }
    },
    {
        "name": "get_action_history",
        "description": "Retrieve the complete audit history of confirmed, executed, and rejected financial actions for the authenticated user.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "get_financial_health_score",
        "description": "Evaluate and return the deterministic 7-factor financial health score (0-100) with detailed component breakdown.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "get_financial_intelligence",
        "description": "Retrieve unified master financial intelligence combining health scores, forecasts, risks, goals, smart actions, and proactive insights.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "explain_financial_forecast",
        "description": "Provide a transparent mathematical explanation for the user's next-month cashflow, expense, and savings forecast.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "explain_financial_risk",
        "description": "Explain why a specific financial risk or stress flag was triggered with verified evidence citations.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    },
    {
        "name": "explain_goal_status",
        "description": "Explain the progress velocity, timeline feasibility, and behind/ahead status calculation for financial goals.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "goal_id": {
                    "type": "INTEGER",
                    "description": "Optional goal ID to explain."
                }
            }
        }
    },
    {
        "name": "explain_smart_action",
        "description": "Explain why a specific Smart Action was proposed, including triggered rules, baseline evidence, and expected impact.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "action_id": {
                    "type": "STRING",
                    "description": "Action ID to explain."
                }
            }
        }
    },
    {
        "name": "run_financial_simulation",
        "description": "Execute a hypothetical what-if financial decision simulation (e.g. INCREASE_SAVINGS, REDUCE_EXPENSES, INCOME_INCREASE) with zero database modifications.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "scenario": {
                    "type": "STRING",
                    "description": "Scenario type: INCREASE_SAVINGS, REDUCE_EXPENSES, INCREASE_EXPENSES, INCOME_REDUCTION, INCOME_INCREASE, GOAL_DEADLINE_CHANGE, MONTHLY_CONTRIBUTION_CHANGE, DEBT_PAYMENT_CHANGE."
                },
                "amount": {
                    "type": "NUMBER",
                    "description": "Optional monetary delta amount."
                },
                "percentage": {
                    "type": "NUMBER",
                    "description": "Optional percentage delta."
                },
                "months": {
                    "type": "INTEGER",
                    "description": "Optional timeline delta in months."
                }
            },
            "required": ["scenario"]
        }
    },
    {
        "name": "explain_health_score",
        "description": "Explain the exact deterministic scoring breakdown, weights, and limiting factors for the user's Financial Health Score.",
        "parameters": {
            "type": "OBJECT",
            "properties": {}
        }
    }
]

