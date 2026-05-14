from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.data import TRAINING_BORROWERS
from app.schemas import Borrower
from app.scoring import assess_term, clamp, estimate_monthly_payment

APPROVAL_THRESHOLD = 0.55


def _borrower_features(borrower: Borrower) -> dict[str, Any]:
    loan_to_income = borrower.loan_amount / borrower.income if borrower.income else 0
    monthly_payment = estimate_monthly_payment(
        borrower.loan_amount,
        borrower.interest_rate,
        borrower.loan_term_months,
    )
    payment_to_income = monthly_payment / borrower.income if borrower.income else 1
    return {
        "age": borrower.age,
        "income": borrower.income,
        "employment_years": borrower.employment_years,
        "loan_amount": borrower.loan_amount,
        "loan_term_months": borrower.loan_term_months,
        "interest_rate": borrower.interest_rate,
        "debt_load": borrower.debt_load,
        "loan_to_income": loan_to_income,
        "payment_to_income": payment_to_income,
        "past_defaults": int(borrower.past_defaults),
        "employment_type": borrower.employment_type,
        "housing_type": borrower.housing_type,
        "credit_history": borrower.credit_history,
    }


def _synthetic_label(borrower: Borrower) -> int:
    features = _borrower_features(borrower)
    risk = 0.22
    risk += 0.18 if features["payment_to_income"] > 0.42 else 0
    risk += 0.14 if features["debt_load"] > 0.52 else -0.05
    risk += 0.13 if features["loan_to_income"] > 12 else -0.04
    risk += 0.13 if borrower.credit_history == "poor" else 0
    risk += 0.09 if borrower.credit_history == "late_payments" else 0
    risk -= 0.08 if borrower.credit_history == "excellent" else 0
    risk += 0.18 if borrower.past_defaults else 0
    risk += 0.08 if borrower.employment_type in {"temporary", "unemployed"} else 0
    risk -= 0.05 if borrower.employment_type == "full_time" else 0
    risk -= 0.05 if borrower.housing_type == "own" else 0
    risk += 0.04 if borrower.age < 25 else 0
    risk += 0.04 if borrower.loan_term_months >= 60 else 0
    return int(clamp(risk) >= APPROVAL_THRESHOLD)


@lru_cache(maxsize=1)
def _build_model() -> Any:
    try:
        from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier, VotingClassifier
        from sklearn.feature_extraction import DictVectorizer
        from sklearn.pipeline import Pipeline
    except ImportError as exc:
        raise RuntimeError("Install scikit-learn to use the classic ML scorer") from exc

    model = VotingClassifier(
        estimators=[
            (
                "random_forest",
                RandomForestClassifier(
                    n_estimators=160,
                    max_depth=6,
                    min_samples_leaf=6,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
            (
                "gradient_boosting",
                GradientBoostingClassifier(
                    n_estimators=90,
                    learning_rate=0.045,
                    max_depth=2,
                    subsample=0.85,
                    random_state=42,
                ),
            ),
        ],
        voting="soft",
        weights=[0.55, 0.45],
    )
    pipeline = Pipeline(
        steps=[
            ("features", DictVectorizer(sparse=False)),
            ("model", model),
        ]
    )
    x_train = [_borrower_features(borrower) for borrower in TRAINING_BORROWERS]
    y_train = [_synthetic_label(borrower) for borrower in TRAINING_BORROWERS]
    pipeline.fit(x_train, y_train)
    return pipeline


def _factor(name: str, sign: str, impact: float) -> dict[str, Any]:
    return {"name": name, "sign": sign, "impact": round(abs(impact), 3)}


def _explain_features(borrower: Borrower, probability: float) -> list[dict[str, Any]]:
    features = _borrower_features(borrower)
    candidates: list[dict[str, Any]] = []

    if features["payment_to_income"] >= 0.42:
        candidates.append(_factor("высокая доля платежа от дохода", "+", 0.16))
    elif features["payment_to_income"] <= 0.25:
        candidates.append(_factor("комфортная доля платежа от дохода", "-", 0.1))

    if borrower.debt_load >= 0.5:
        candidates.append(_factor("высокая кредитная нагрузка", "+", 0.15))
    elif borrower.debt_load <= 0.3:
        candidates.append(_factor("низкая кредитная нагрузка", "-", 0.08))

    if features["loan_to_income"] >= 12:
        candidates.append(_factor("крупная сумма кредита относительно дохода", "+", 0.12))
    elif features["loan_to_income"] <= 7:
        candidates.append(_factor("умеренная сумма кредита относительно дохода", "-", 0.06))

    if borrower.credit_history in {"poor", "late_payments"}:
        candidates.append(_factor("проблемная кредитная история", "+", 0.14))
    elif borrower.credit_history == "excellent":
        candidates.append(_factor("отличная кредитная история", "-", 0.12))

    if borrower.past_defaults:
        candidates.append(_factor("прошлые дефолты", "+", 0.18))

    if borrower.employment_type in {"temporary", "unemployed"}:
        candidates.append(_factor("нестабильная занятость", "+", 0.08))
    elif borrower.employment_type == "full_time" and borrower.employment_years >= 3:
        candidates.append(_factor("стабильная занятость", "-", 0.07))

    if borrower.loan_term_months >= 60:
        candidates.append(_factor("длинный срок кредита", "+", 0.05))

    if not candidates:
        sign = "+" if probability >= APPROVAL_THRESHOLD else "-"
        candidates.append(_factor("совокупный профиль заемщика", sign, 0.05))

    return sorted(candidates, key=lambda item: item["impact"], reverse=True)[:5]


def score_with_classic_ml(borrower: Borrower | dict[str, Any]) -> dict[str, Any]:
    if isinstance(borrower, dict):
        borrower = Borrower.model_validate(borrower)

    model = _build_model()
    features = _borrower_features(borrower)
    probability = float(model.predict_proba([features])[0][1])
    probability = round(clamp(probability), 2)
    borrower_class = "bad" if probability >= APPROVAL_THRESHOLD else "good"
    recommendation = "отказать" if borrower_class == "bad" else "одобрить"

    monthly_payment = estimate_monthly_payment(
        borrower.loan_amount,
        borrower.interest_rate,
        borrower.loan_term_months,
    )
    payment_to_income = monthly_payment / borrower.income if borrower.income else 1

    return {
        "defaultProbability": probability,
        "borrowerClass": borrower_class,
        "recommendation": recommendation,
        "factors": _explain_features(borrower, probability),
        "loanMetrics": {
            "monthlyPayment": round(monthly_payment, 2),
            "paymentToIncome": round(payment_to_income, 3),
            "termAssessment": assess_term(borrower.loan_term_months, payment_to_income),
        },
    }
