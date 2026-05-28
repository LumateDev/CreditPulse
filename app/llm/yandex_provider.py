from __future__ import annotations

import json
import re
from typing import Any

from app.config import settings
from app.llm.base import LLMProvider


APPROVE = "одобрить"
DECLINE = "отказать"


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
            "Верни только JSON без markdown и без поясняющего текста. "
            "Схема JSON: "
            "defaultProbability number от 0 до 1, borrowerClass good|bad, "
            "recommendation одобрить|отказать, riskLevel low|medium|high, "
            "confidence number от 0 до 1, reasoningSummary короткая строка.\n"
            f"Заемщик: {json.dumps(borrower, ensure_ascii=False)}\n"
            f"Расчетные метрики: {json.dumps(result.get('loanMetrics', {}), ensure_ascii=False)}"
        )

        response = self._client.responses.create(
            prompt={"id": settings.yandex_prompt_id},
            input=prompt_input,
        )
        raw_text = response.output_text.strip()
        parsed = _extract_json_object(raw_text)
        if parsed is None:
            return _fallback_assessment(payload, raw_text)

        try:
            probability = max(0.01, min(0.99, float(parsed["defaultProbability"])))
        except (KeyError, TypeError, ValueError):
            return _fallback_assessment(payload, raw_text)

        recommendation = _normalize_recommendation(parsed.get("recommendation"), probability)
        borrower_class = "bad" if recommendation == DECLINE else "good"
        risk_level = str(parsed.get("riskLevel", "medium"))
        if risk_level not in {"low", "medium", "high"}:
            risk_level = _risk_level(probability)

        try:
            confidence = round(max(0, min(1, float(parsed.get("confidence", 0.5)))), 2)
        except (TypeError, ValueError):
            confidence = 0.5

        return {
            "defaultProbability": round(probability, 2),
            "borrowerClass": borrower_class,
            "recommendation": recommendation,
            "riskLevel": risk_level,
            "confidence": confidence,
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
            f"Вопрос пользователя: {question}\n"
            f"Заемщик: {borrower['name']}\n"
            f"Доход: {borrower['income']}\n"
            f"Сумма кредита: {borrower['loanAmount']}\n"
            f"Срок кредита: {borrower['loanTermMonths']} месяцев\n"
            f"Процентная ставка: {borrower['interestRate']}%\n"
            f"Расчетный ежемесячный платеж: {metrics.get('monthlyPayment')}\n"
            f"Доля платежа от дохода: {metrics.get('paymentToIncome')}\n"
            f"Оценка срока: {metrics.get('termAssessment')}\n"
            f"Решение baseline: {result['recommendation']}\n"
            f"Вероятность дефолта baseline: {result['defaultProbability']}\n"
            f"Факторы baseline: {factors}\n"
            f"Classic ML: {ml_result}\n"
            f"LLM assessment: {ai_assessment}\n"
            f"Сравнение: {comparison}\n"
            "Если вопрос пользователя касается срока, возврата или платежа, сначала прямо ответь "
            "на этот вопрос с опорой на срок, расчетный платеж и долю платежа от дохода. "
            "Затем коротко добавь итоговую рекомендацию. Если есть classic ML и LLM assessment, "
            "объясни совпадение или расхождение между ними. Если вопрос общий, объясни решение по заявке."
        )

        response = self._client.responses.create(
            prompt={"id": settings.yandex_prompt_id},
            input=prompt_input,
        )
        return response.output_text.strip()


def _extract_json_object(raw_text: str) -> dict[str, Any] | None:
    text = raw_text.strip()
    if not text:
        return None

    candidates = [text]
    candidates.extend(
        re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    )

    first = text.find("{")
    last = text.rfind("}")
    if first != -1 and last > first:
        candidates.append(text[first : last + 1])

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def _fallback_assessment(payload: dict[str, Any], raw_text: str = "") -> dict[str, Any]:
    result = payload.get("result", {})
    probability = max(0.01, min(0.99, float(result.get("defaultProbability", 0.5))))
    recommendation = _normalize_recommendation(result.get("recommendation"), probability)
    summary = raw_text.strip()
    if not summary:
        factors = result.get("factors", [])
        factor_names = [
            str(factor.get("name", "")) for factor in factors[:2] if factor.get("name")
        ]
        summary = (
            "Ключевые факторы: " + ", ".join(factor_names)
            if factor_names
            else "LLM-оценка заменена расчетной базовой оценкой."
        )

    return {
        "defaultProbability": round(probability, 2),
        "borrowerClass": "bad" if recommendation == DECLINE else "good",
        "recommendation": recommendation,
        "riskLevel": _risk_level(probability),
        "confidence": 0.5,
        "reasoningSummary": summary[:500],
    }


def _normalize_recommendation(value: Any, probability: float) -> str:
    recommendation = str(value or "").strip().lower()
    if recommendation in {APPROVE, "approve", "approved", "good"}:
        return APPROVE
    if recommendation in {DECLINE, "decline", "reject", "rejected", "bad"}:
        return DECLINE
    return DECLINE if probability >= 0.55 else APPROVE


def _risk_level(probability: float) -> str:
    if probability >= 0.55:
        return "high"
    if probability >= 0.35:
        return "medium"
    return "low"
