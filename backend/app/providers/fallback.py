import logging
from collections.abc import AsyncGenerator

from app.providers.base import LLMProvider, LLMResponse
from app.providers.exceptions import (
    ProviderConfigurationError,
    ProviderError,
    ProviderUnavailableError,
)

logger = logging.getLogger(__name__)


class FallbackLLMProvider(LLMProvider):
    """
    Ordered LLM provider fallback.

    The primary provider is attempted first. Retryable failures cause
    the fallback provider to be attempted only when the primary fails
    before producing any streaming output.

    Example:

        Ollama -> Anthropic
    """

    def __init__(
        self,
        primary: LLMProvider,
        fallback: LLMProvider | None = None,
    ):
        self.primary = primary
        self.fallback = fallback

        self.last_provider: str | None = None
        self.last_model: str | None = None

    @property
    def provider_name(self) -> str:
        return self.last_provider or self.primary.provider_name

    @property
    def model(self) -> str:
        return self.last_model or self.primary.model

    def _record_response(
        self,
        response: LLMResponse,
    ) -> LLMResponse:
        self.last_provider = response.provider
        self.last_model = response.model

        return response

    def _record_provider(
        self,
        provider: LLMProvider,
    ) -> None:
        self.last_provider = provider.provider_name
        self.last_model = provider.model

    async def generate(
        self,
        system_prompt: str,
        user_message: str,
    ) -> LLMResponse:
        try:
            response = await self.primary.generate(
                system_prompt=system_prompt,
                user_message=user_message,
            )

            return self._record_response(response)

        except ProviderError as primary_error:
            if not primary_error.retryable:
                raise

            if self.fallback is None:
                raise

            logger.warning(
                "Primary LLM provider failed; attempting fallback",
                extra={
                    "primary_provider": self.primary.provider_name,
                    "primary_model": self.primary.model,
                    "fallback_provider": self.fallback.provider_name,
                    "fallback_model": self.fallback.model,
                    "error_type": type(primary_error).__name__,
                },
            )

            try:
                response = await self.fallback.generate(
                    system_prompt=system_prompt,
                    user_message=user_message,
                )

                logger.info(
                    "LLM fallback provider succeeded",
                    extra={
                        "provider": response.provider,
                        "model": response.model,
                    },
                )

                return self._record_response(response)

            except ProviderConfigurationError:
                raise primary_error

            except ProviderError as fallback_error:
                logger.error(
                    "All configured LLM providers failed",
                    extra={
                        "primary_provider": self.primary.provider_name,
                        "fallback_provider": self.fallback.provider_name,
                        "primary_error": type(primary_error).__name__,
                        "fallback_error": type(fallback_error).__name__,
                    },
                )

                raise ProviderUnavailableError(
                    (
                        "All configured LLM providers are "
                        "currently unavailable. "
                        f"Primary provider: "
                        f"{self.primary.provider_name}. "
                        f"Fallback provider: "
                        f"{self.fallback.provider_name}."
                    ),
                    provider=self.primary.provider_name,
                ) from fallback_error

    async def stream(
        self,
        system_prompt: str,
        user_message: str,
    ) -> AsyncGenerator[str, None]:
        self._record_provider(self.primary)
        primary_started_output = False

        try:
            async for token in self.primary.stream(
                system_prompt=system_prompt,
                user_message=user_message,
            ):
                primary_started_output = True
                yield token

            return

        except ProviderError as primary_error:
            if primary_started_output:
                logger.error(
                    "Primary LLM streaming provider failed after "
                    "partial output; fallback disabled",
                    extra={
                        "provider": self.primary.provider_name,
                        "model": self.primary.model,
                        "error_type": type(primary_error).__name__,
                    },
                )
                raise

            if not primary_error.retryable:
                raise

            if self.fallback is None:
                raise

            logger.warning(
                "Primary LLM streaming provider failed before output; "
                "attempting fallback",
                extra={
                    "primary_provider": self.primary.provider_name,
                    "primary_model": self.primary.model,
                    "fallback_provider": self.fallback.provider_name,
                    "fallback_model": self.fallback.model,
                    "error_type": type(primary_error).__name__,
                },
            )

            try:
                self._record_provider(self.fallback)

                async for token in self.fallback.stream(
                    system_prompt=system_prompt,
                    user_message=user_message,
                ):
                    yield token

                logger.info(
                    "LLM streaming fallback provider succeeded",
                    extra={
                        "provider": self.fallback.provider_name,
                        "model": self.fallback.model,
                    },
                )

            except ProviderConfigurationError:
                raise primary_error

            except ProviderError as fallback_error:
                logger.error(
                    "All configured LLM streaming providers failed",
                    extra={
                        "primary_provider": self.primary.provider_name,
                        "fallback_provider": self.fallback.provider_name,
                        "primary_error": type(primary_error).__name__,
                        "fallback_error": type(fallback_error).__name__,
                    },
                )

                raise ProviderUnavailableError(
                    (
                        "All configured LLM providers are "
                        "currently unavailable. "
                        f"Primary provider: "
                        f"{self.primary.provider_name}. "
                        f"Fallback provider: "
                        f"{self.fallback.provider_name}."
                    ),
                    provider=self.primary.provider_name,
                ) from fallback_error
