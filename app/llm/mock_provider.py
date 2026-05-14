from __future__ import annotations

from typing import Any

from app.llm.base import LLMProvider


def format_money(value: float) -> str:
    return f"{value:,.0f} ₽".replace(",", " ")


class MockLLMProvider(LLMProvider):
    def assess(self, payload: dict[str, Any]) -> dict[str, Any]:
        borrower = payload["borrower"]
        risk = 0.24
        income = float(borrower["income"])
        loan_amount = float(borrower["loanAmount"])
        debt_load = float(borrower["debtLoad"])
        payment_to_income = float(payload.get("result", {}).get("loanMetrics", {}).get("paymentToIncome", 0))

        if payment_to_income >= 0.42:
            risk += 0.16
        elif payment_to_income <= 0.25:
            risk -= 0.08

        if debt_load >= 0.5:
            risk += 0.14
        elif debt_load <= 0.3:
            risk -= 0.07

        if income > 0 and loan_amount / income >= 12:
            risk += 0.1
        elif income > 0 and loan_amount / income <= 7:
            risk -= 0.05

        if borrower["creditHistory"] == "excellent":
            risk -= 0.11
        elif borrower["creditHistory"] == "good":
            risk -= 0.05
        elif borrower["creditHistory"] == "late_payments":
            risk += 0.11
        elif borrower["creditHistory"] == "poor":
            risk += 0.17

        if borrower["pastDefaults"]:
            risk += 0.19
        if borrower["employmentType"] in {"temporary", "unemployed"}:
            risk += 0.08
        if borrower["loanTermMonths"] >= 60:
            risk += 0.04

        probability = round(max(0.01, min(0.99, risk)), 2)
        recommendation = "отказать" if probability >= 0.55 else "одобрить"
        risk_level = "high" if probability >= 0.55 else "medium" if probability >= 0.35 else "low"
        summary = (
            "LLM-оценка видит высокий риск и предлагает отказ."
            if recommendation == "отказать"
            else "LLM-оценка считает профиль приемлемым для одобрения."
        )
        return {
            "defaultProbability": probability,
            "borrowerClass": "bad" if recommendation == "отказать" else "good",
            "recommendation": recommendation,
            "riskLevel": risk_level,
            "confidence": 0.72,
            "reasoningSummary": summary,
        }

    def explain(self, payload: dict[str, Any]) -> str:
        result = payload["result"]
        ml_result = payload.get("mlResult")
        ai_assessment = payload.get("aiAssessment")
        comparison = payload.get("comparison")
        factors = result.get("factors", [])
        recommendation = result["recommendation"]
        probability = result["defaultProbability"]
        question = payload.get("question", "").lower()
        metrics = result.get("loanMetrics", {})

        risky = [factor["name"] for factor in factors if factor["sign"] == "+"]
        protective = [factor["name"] for factor in factors if factor["sign"] == "-"]

        if any(word in question for word in ("срок", "возврат", "платеж", "платёж")):
            monthly_payment = format_money(float(metrics.get("monthlyPayment", 0)))
            payment_share = round(float(metrics.get("paymentToIncome", 0)) * 100)
            term_assessment = metrics.get("termAssessment", "срок требует дополнительной проверки")
            return (
                f"По сроку возврата: расчетный ежемесячный платеж составит примерно {monthly_payment}, "
                f"это около {payment_share}% дохода заемщика. {term_assessment.capitalize()}. "
                f"Итоговая рекомендация по заявке — {recommendation}."
            )

        if ml_result and ai_assessment and comparison:
            return (
                f"Classic ML оценивает риск дефолта в {ml_result['defaultProbability']:.2f} "
                f"и рекомендует {ml_result['recommendation']}. "
                f"LLM как второе мнение оценивает риск в {ai_assessment['defaultProbability']:.2f} "
                f"и рекомендует {ai_assessment['recommendation']}. "
                f"{comparison['summary']}"
            )

        if recommendation == "отказать":
            main = risky[0] if risky else "повышенная вероятность дефолта"
            extra = ", ".join(risky[1:3]) if len(risky) > 1 else "совокупность параметров заявки"
            return (
                f"Основная причина отказа — {main}, из-за чего риск дефолта оценивается "
                f"на уровне {probability:.2f}. Дополнительно учитываются {extra}. "
                "В связи с этим рекомендуется отказать в выдаче кредита."
            )

        main = protective[0] if protective else "приемлемый уровень риска"
        extra = ", ".join(protective[1:3]) if len(protective) > 1 else "отсутствие критичных негативных факторов"
        return (
            f"Заявку можно одобрить, так как ключевой положительный фактор — {main}, "
            f"а риск дефолта оценивается на уровне {probability:.2f}. "
            f"Также учитываются {extra}. Итоговая рекомендация — одобрить кредит."
        )
