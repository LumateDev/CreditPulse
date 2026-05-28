from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.schemas import Borrower


@dataclass(frozen=True)
class Factor:
    name: str
    sign: str
    impact: float


def clamp(value: float, low: float = 0.01, high: float = 0.99) -> float:
    return max(low, min(high, value))


def estimate_monthly_payment(amount: float, annual_rate: float, months: int) -> float:
    if months <= 0:
        return amount
    monthly_rate = annual_rate / 100 / 12
    if monthly_rate <= 0:
        return amount / months
    multiplier = (1 + monthly_rate) ** months
    return amount * monthly_rate * multiplier / (multiplier - 1)


def assess_term(months: int, payment_to_income: float) -> str:
    if payment_to_income >= 0.45:
        return "\u0441\u0440\u043e\u043a \u0432\u044b\u0433\u043b\u044f\u0434\u0438\u0442 \u043d\u0430\u043f\u0440\u044f\u0436\u0435\u043d\u043d\u044b\u043c: \u0440\u0430\u0441\u0447\u0435\u0442\u043d\u044b\u0439 \u043f\u043b\u0430\u0442\u0435\u0436 \u0437\u0430\u043d\u0438\u043c\u0430\u0435\u0442 \u0441\u043b\u0438\u0448\u043a\u043e\u043c \u0431\u043e\u043b\u044c\u0448\u0443\u044e \u0434\u043e\u043b\u044e \u0434\u043e\u0445\u043e\u0434\u0430"
    if months >= 48:
        return "\u0441\u0440\u043e\u043a \u0434\u043b\u0438\u043d\u043d\u044b\u0439, \u043f\u043b\u0430\u0442\u0435\u0436 \u043d\u0438\u0436\u0435, \u043d\u043e \u0437\u0430\u0435\u043c\u0449\u0438\u043a \u0434\u043e\u043b\u044c\u0448\u0435 \u043e\u0441\u0442\u0430\u0435\u0442\u0441\u044f \u043f\u043e\u0434 \u0434\u043e\u043b\u0433\u043e\u0432\u043e\u0439 \u043d\u0430\u0433\u0440\u0443\u0437\u043a\u043e\u0439"
    if months <= 24 and payment_to_income <= 0.3:
        return "\u0441\u0440\u043e\u043a \u0432\u044b\u0433\u043b\u044f\u0434\u0438\u0442 \u043a\u043e\u043c\u0444\u043e\u0440\u0442\u043d\u044b\u043c \u043e\u0442\u043d\u043e\u0441\u0438\u0442\u0435\u043b\u044c\u043d\u043e \u0434\u043e\u0445\u043e\u0434\u0430 \u0438 \u0440\u0430\u0441\u0447\u0435\u0442\u043d\u043e\u0433\u043e \u043f\u043b\u0430\u0442\u0435\u0436\u0430"
    return "\u0441\u0440\u043e\u043a \u0432\u044b\u0433\u043b\u044f\u0434\u0438\u0442 \u0443\u043c\u0435\u0440\u0435\u043d\u043d\u044b\u043c, \u043a\u0440\u0438\u0442\u0438\u0447\u043d\u043e\u0439 \u043d\u0430\u0433\u0440\u0443\u0437\u043a\u0438 \u043f\u043e \u0440\u0430\u0441\u0447\u0435\u0442\u043d\u043e\u043c\u0443 \u043f\u043b\u0430\u0442\u0435\u0436\u0443 \u043d\u0435 \u0432\u0438\u0434\u043d\u043e"


def score_borrower(borrower: Borrower | dict[str, Any]) -> dict[str, Any]:
    """Deterministic baseline scoring used until the trained AI module is ready."""
    if isinstance(borrower, dict):
        borrower = Borrower.model_validate(borrower)

    risk = 0.28
    factors: list[Factor] = []

    def add(name: str, delta: float) -> None:
        nonlocal risk
        risk += delta
        factors.append(Factor(name=name, sign="+" if delta > 0 else "-", impact=round(delta, 3)))

    income = borrower.income
    loan_amount = borrower.loan_amount
    employment_years = borrower.employment_years
    debt_load = borrower.debt_load
    age = borrower.age
    credit_history = borrower.credit_history
    housing_type = borrower.housing_type
    employment_type = borrower.employment_type
    past_defaults = borrower.past_defaults
    interest_rate = borrower.interest_rate
    term = borrower.loan_term_months

    if income < 45000:
        add("\u043d\u0438\u0437\u043a\u0438\u0439 \u0434\u043e\u0445\u043e\u0434", 0.16)
    elif income > 110000:
        add("\u0432\u044b\u0441\u043e\u043a\u0438\u0439 \u0434\u043e\u0445\u043e\u0434", -0.1)

    if income > 0 and loan_amount / income > 14:
        add("\u0432\u044b\u0441\u043e\u043a\u0430\u044f \u0441\u0443\u043c\u043c\u0430 \u043a\u0440\u0435\u0434\u0438\u0442\u0430 \u043e\u0442\u043d\u043e\u0441\u0438\u0442\u0435\u043b\u044c\u043d\u043e \u0434\u043e\u0445\u043e\u0434\u0430", 0.13)
    elif income > 0 and loan_amount / income < 7:
        add("\u0443\u043c\u0435\u0440\u0435\u043d\u043d\u0430\u044f \u0441\u0443\u043c\u043c\u0430 \u043a\u0440\u0435\u0434\u0438\u0442\u0430 \u043e\u0442\u043d\u043e\u0441\u0438\u0442\u0435\u043b\u044c\u043d\u043e \u0434\u043e\u0445\u043e\u0434\u0430", -0.06)

    if debt_load >= 0.5:
        add("\u0432\u044b\u0441\u043e\u043a\u0430\u044f \u043a\u0440\u0435\u0434\u0438\u0442\u043d\u0430\u044f \u043d\u0430\u0433\u0440\u0443\u0437\u043a\u0430", 0.18)
    elif debt_load <= 0.3:
        add("\u043d\u0438\u0437\u043a\u0430\u044f \u043a\u0440\u0435\u0434\u0438\u0442\u043d\u0430\u044f \u043d\u0430\u0433\u0440\u0443\u0437\u043a\u0430", -0.08)

    if employment_years < 1:
        add("\u043e\u0447\u0435\u043d\u044c \u043d\u0435\u0431\u043e\u043b\u044c\u0448\u043e\u0439 \u0441\u0442\u0430\u0436 \u0440\u0430\u0431\u043e\u0442\u044b", 0.12)
    elif employment_years < 2:
        add("\u043d\u0435\u0431\u043e\u043b\u044c\u0448\u043e\u0439 \u0441\u0442\u0430\u0436 \u0440\u0430\u0431\u043e\u0442\u044b", 0.07)
    elif employment_years >= 5:
        add("\u0441\u0442\u0430\u0431\u0438\u043b\u044c\u043d\u044b\u0439 \u0441\u0442\u0430\u0436 \u0440\u0430\u0431\u043e\u0442\u044b", -0.08)

    if credit_history == "excellent":
        add("\u043e\u0442\u043b\u0438\u0447\u043d\u0430\u044f \u043a\u0440\u0435\u0434\u0438\u0442\u043d\u0430\u044f \u0438\u0441\u0442\u043e\u0440\u0438\u044f", -0.12)
    elif credit_history == "good":
        add("\u0445\u043e\u0440\u043e\u0448\u0430\u044f \u043a\u0440\u0435\u0434\u0438\u0442\u043d\u0430\u044f \u0438\u0441\u0442\u043e\u0440\u0438\u044f", -0.07)
    elif credit_history == "late_payments":
        add("\u043d\u0430\u043b\u0438\u0447\u0438\u0435 \u043f\u0440\u043e\u0441\u0440\u043e\u0447\u0435\u043a", 0.12)
    elif credit_history == "poor":
        add("\u0441\u043b\u0430\u0431\u0430\u044f \u043a\u0440\u0435\u0434\u0438\u0442\u043d\u0430\u044f \u0438\u0441\u0442\u043e\u0440\u0438\u044f", 0.18)

    if past_defaults:
        add("\u043d\u0430\u043b\u0438\u0447\u0438\u0435 \u043f\u0440\u043e\u0448\u043b\u044b\u0445 \u0434\u0435\u0444\u043e\u043b\u0442\u043e\u0432", 0.2)

    if employment_type in {"temporary", "unemployed"}:
        add("\u043d\u0435\u0441\u0442\u0430\u0431\u0438\u043b\u044c\u043d\u044b\u0439 \u0442\u0438\u043f \u0437\u0430\u043d\u044f\u0442\u043e\u0441\u0442\u0438", 0.1)
    elif employment_type == "part_time":
        add("\u0447\u0430\u0441\u0442\u0438\u0447\u043d\u0430\u044f \u0437\u0430\u043d\u044f\u0442\u043e\u0441\u0442\u044c", 0.05)
    elif employment_type == "full_time":
        add("\u043f\u043e\u0441\u0442\u043e\u044f\u043d\u043d\u0430\u044f \u0437\u0430\u043d\u044f\u0442\u043e\u0441\u0442\u044c", -0.04)

    if housing_type == "own":
        add("\u0441\u043e\u0431\u0441\u0442\u0432\u0435\u043d\u043d\u043e\u0435 \u0436\u0438\u043b\u044c\u0435", -0.05)
    elif housing_type == "parents":
        add("\u043f\u0440\u043e\u0436\u0438\u0432\u0430\u043d\u0438\u0435 \u0443 \u0440\u043e\u0434\u0438\u0442\u0435\u043b\u0435\u0439", -0.02)
    elif housing_type == "rent":
        add("\u0430\u0440\u0435\u043d\u0434\u043d\u043e\u0435 \u0436\u0438\u043b\u044c\u0435", 0.04)

    if interest_rate >= 20:
        add("\u0432\u044b\u0441\u043e\u043a\u0430\u044f \u043f\u0440\u043e\u0446\u0435\u043d\u0442\u043d\u0430\u044f \u0441\u0442\u0430\u0432\u043a\u0430", 0.06)

    if term >= 48:
        add("\u0434\u043b\u0438\u0442\u0435\u043b\u044c\u043d\u044b\u0439 \u0441\u0440\u043e\u043a \u043a\u0440\u0435\u0434\u0438\u0442\u0430", 0.05)

    if age < 25:
        add("\u043c\u043e\u043b\u043e\u0434\u043e\u0439 \u0432\u043e\u0437\u0440\u0430\u0441\u0442 \u0437\u0430\u0435\u043c\u0449\u0438\u043a\u0430", 0.04)

    monthly_payment = estimate_monthly_payment(loan_amount, interest_rate, term)
    payment_to_income = monthly_payment / income if income else 1
    probability = round(clamp(risk), 2)
    decision = "\u043e\u0442\u043a\u0430\u0437\u0430\u0442\u044c" if probability >= 0.55 else "\u043e\u0434\u043e\u0431\u0440\u0438\u0442\u044c"
    borrower_class = "bad" if probability >= 0.55 else "good"

    top_factors = sorted(factors, key=lambda item: abs(item.impact), reverse=True)[:5]
    return {
        "defaultProbability": probability,
        "borrowerClass": borrower_class,
        "recommendation": decision,
        "factors": [factor.__dict__ for factor in top_factors],
        "loanMetrics": {
            "monthlyPayment": round(monthly_payment, 2),
            "paymentToIncome": round(payment_to_income, 3),
            "termAssessment": assess_term(term, payment_to_income),
        },
    }
