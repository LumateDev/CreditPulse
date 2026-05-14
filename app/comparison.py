from __future__ import annotations

from typing import Any


def compare_predictions(ml_result: dict[str, Any], ai_assessment: dict[str, Any]) -> dict[str, Any]:
    probability_gap = round(
        abs(
            float(ml_result["defaultProbability"])
            - float(ai_assessment["defaultProbability"])
        ),
        2,
    )
    agreement = ml_result["recommendation"] == ai_assessment["recommendation"]

    if agreement and probability_gap <= 0.12:
        summary = "ML и LLM дают близкую оценку риска и одинаковую рекомендацию."
    elif agreement:
        summary = "Рекомендации совпали, но оценка вероятности риска заметно отличается."
    else:
        summary = "ML и LLM расходятся в рекомендации, заявку стоит отправить на ручную проверку."

    return {
        "agreement": agreement,
        "probabilityGap": probability_gap,
        "summary": summary,
    }
