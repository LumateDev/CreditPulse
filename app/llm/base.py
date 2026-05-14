from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    @abstractmethod
    def explain(self, payload: dict[str, Any]) -> str:
        """Return a short human explanation for a scoring result."""
