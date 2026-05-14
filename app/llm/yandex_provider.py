from __future__ import annotations

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

    def explain(self, payload: dict[str, Any]) -> str:
        result = payload["result"]
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
            "Если вопрос пользователя касается срока, возврата или платежа, сначала прямо ответь "
            "на этот вопрос с опорой на срок, расчетный платеж и долю платежа от дохода. "
            "Затем коротко добавь итоговую рекомендацию. Если вопрос общий, объясни решение по форме."
        )

        response = self._client.responses.create(
            prompt={"id": settings.yandex_prompt_id},
            input=prompt_input,
        )
        return response.output_text.strip()
