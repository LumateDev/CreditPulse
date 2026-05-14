from __future__ import annotations

import json
from typing import Any

from app.config import settings
from app.llm.base import LLMProvider


class YandexLLMProvider(LLMProvider):
    def __init__(self) -> None:
        if not settings.yandex_api_key:
            raise RuntimeError("YANDEX_API_KEY is required for yandex provider")

        try:
            import openai
        except ImportError as exc:
            raise RuntimeError("Install the openai package to use yandex provider") from exc

        self._client = openai.OpenAI(
            api_key=settings.yandex_api_key,
            base_url=settings.yandex_base_url,
            project=settings.yandex_project,
        )

    def assess(self, payload: dict[str, Any]) -> dict[str, Any]:
        borrower = payload["borrower"]
        result = payload.get("result", {})
        prompt_input = (
            "Оцени кредитный риск заемщика как независимое LLM-мнение. "
            "Верни только JSON без markdown и без поясняющего текста с полями: "
            "defaultProbability number от 0 до 1, borrowerClass good|bad, "
            "recommendation одобрить|отказать, riskLevel low|medium|high, "
            "confidence number от 0 до 1, reasoningSummary короткая строка.\n"
            f"заемщик: {json.dumps(borrower, ensure_ascii=False)}\n"
            f"расчетные метрики: {json.dumps(result.get('loanMetrics', {}), ensure_ascii=False)}"
        )

        response = self._client.responses.create(
            prompt={"id": settings.yandex_prompt_id},
            input=prompt_input,
        )
        raw_text = response.output_text.strip()
        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"LLM returned non-JSON assessment: {raw_text}") from exc

        probability = max(0.01, min(0.99, float(parsed["defaultProbability"])))
        recommendation = str(parsed["recommendation"])
        if recommendation not in {"одобрить", "отказать"}:
            recommendation = "отказать" if probability >= 0.55 else "одобрить"
        borrower_class = "bad" if recommendation == "отказать" else "good"
        risk_level = str(parsed.get("riskLevel", "medium"))
        if risk_level not in {"low", "medium", "high"}:
            risk_level = "high" if probability >= 0.55 else "medium" if probability >= 0.35 else "low"
        return {
            "defaultProbability": round(probability, 2),
            "borrowerClass": borrower_class,
            "recommendation": recommendation,
            "riskLevel": risk_level,
            "confidence": round(max(0, min(1, float(parsed.get("confidence", 0.5)))), 2),
            "reasoningSummary": str(parsed.get("reasoningSummary", "")),
        }

    def explain(self, payload: dict[str, Any]) -> str:
        result = payload["result"]
        ml_result = payload.get("mlResult")
        ai_assessment = payload.get("aiAssessment")
        comparison = payload.get("comparison")
        borrower = payload["borrower"]
        question = payload.get("question", "")
        metrics = result.get("loanMetrics", {})
        factors = ", ".join(
            f'{factor["name"]} ({factor["sign"]})' for factor in result.get("factors", [])
        )
        prompt_input = (
            f"вопрос пользователя: {question}\n"
            f"заемщик: {borrower['name']}\n"
            f"доход: {borrower['income']}\n"
            f"сумма кредита: {borrower['loanAmount']}\n"
            f"срок кредита: {borrower['loanTermMonths']} месяцев\n"
            f"процентная ставка: {borrower['interestRate']}%\n"
            f"расчетный ежемесячный платеж: {metrics.get('monthlyPayment')}\n"
            f"доля платежа от дохода: {metrics.get('paymentToIncome')}\n"
            f"оценка срока: {metrics.get('termAssessment')}\n"
            f"решение: {result['recommendation']}\n"
            f"вероятность дефолта: {result['defaultProbability']}\n"
            f"факторы: {factors}\n"
            f"classic ML: {ml_result}\n"
            f"LLM assessment: {ai_assessment}\n"
            f"сравнение: {comparison}\n"
            "Если вопрос пользователя касается срока, возврата или платежа, сначала прямо ответь "
            "на этот вопрос с опорой на срок, расчетный платеж и долю платежа от дохода. "
            "Затем коротко добавь итоговую рекомендацию. Если есть classic ML и LLM assessment, "
            "объясни совпадение или расхождение между ними. Если вопрос общий, объясни решение по форме."
        )

        response = self._client.responses.create(
            prompt={"id": settings.yandex_prompt_id},
            input=prompt_input,
        )
        return response.output_text.strip()
