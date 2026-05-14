from app.config import settings
from app.llm.base import LLMProvider
from app.llm.mock_provider import MockLLMProvider
from app.llm.yandex_provider import YandexLLMProvider


def build_llm_provider() -> LLMProvider:
    if settings.llm_provider.lower() == "yandex":
        return YandexLLMProvider()
    return MockLLMProvider()
