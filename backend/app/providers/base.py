from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncGenerator


@dataclass
class LLMResponse:
    content: str
    provider: str
    model: str


class LLMProvider(ABC):
    """
    Common interface implemented by every LLM provider.

    Providers are intentionally kept behind this interface so the
    application and agent layer do not depend on a specific vendor.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Stable provider identifier used by the API."""
        raise NotImplementedError

    @property
    @abstractmethod
    def model(self) -> str:
        """Configured model identifier."""
        raise NotImplementedError

    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_message: str,
    ) -> LLMResponse:
        """Generate a complete response."""
        raise NotImplementedError

    @abstractmethod
    async def stream(
        self,
        system_prompt: str,
        user_message: str,
    ) -> AsyncGenerator[str, None]:
        """Stream response tokens."""
        raise NotImplementedError