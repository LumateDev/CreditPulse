from __future__ import annotations

from typing import Any

from app.llm.base import LLMProvider


def format_money(value: float) -> str:
    return f"{value:,.0f} ₽".replace(",", " ")


class MockLLMProvider(LLMProvider):
    def explain(self, payload: dict[str, Any]) -> str:
        result = payload["result"]
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
