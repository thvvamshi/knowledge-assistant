from collections.abc import AsyncGenerator

from anthropic import AsyncAnthropic
from anthropic import APIConnectionError, APIStatusError, APITimeoutError

from app.core.config import get_settings
from app.providers.base import LLMProvider, LLMResponse
from app.providers.exceptions import (
    ProviderConfigurationError,
    ProviderResponseError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)


class AnthropicProvider(LLMProvider):
    """Anthropic cloud LLM provider."""

    def __init__(self):
        settings = get_settings()

        self._api_key = settings.anthropic_api_key
        self._model = settings.anthropic_model

        if not self._api_key:
            raise ProviderConfigurationError(
                "Anthropic API key is not configured.",
                provider="anthropic",
            )

        if not self._model:
            raise ProviderConfigurationError(
                "Anthropic model is not configured.",
                provider="anthropic",
            )

        self.client = AsyncAnthropic(
            api_key=self._api_key,
        )

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def model(self) -> str:
        return self._model

    async def generate(
        self,
        system_prompt: str,
        user_message: str,
    ) -> LLMResponse:
        try:
            response = await self.client.messages.create(
                model=self._model,
                max_tokens=4096,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_message,
                    }
                ],
            )

        except APITimeoutError as exc:
            raise ProviderTimeoutError(
                "Anthropic request timed out.",
                provider="anthropic",
            ) from exc

        except APIConnectionError as exc:
            raise ProviderUnavailableError(
                "Anthropic is unavailable.",
                provider="anthropic",
            ) from exc

        except APIStatusError as exc:
            if exc.status_code >= 500:
                raise ProviderUnavailableError(
                    (
                        "Anthropic returned server error "
                        f"{exc.status_code}."
                    ),
                    provider="anthropic",
                ) from exc

            raise ProviderResponseError(
                (
                    "Anthropic returned HTTP "
                    f"{exc.status_code}."
                ),
                provider="anthropic",
            ) from exc

        except Exception as exc:
            raise ProviderResponseError(
                "Anthropic request failed.",
                provider="anthropic",
            ) from exc

        content_parts = []

        for block in response.content:
            text = getattr(block, "text", None)

            if isinstance(text, str) and text:
                content_parts.append(text)

        content = "".join(content_parts).strip()

        if not content:
            raise ProviderResponseError(
                "Anthropic returned an empty response.",
                provider="anthropic",
            )

        return LLMResponse(
            content=content,
            provider=self.provider_name,
            model=self.model,
        )

    async def stream(
        self,
        system_prompt: str,
        user_message: str,
    ) -> AsyncGenerator[str, None]:
        received_content = False

        try:
            async with self.client.messages.stream(
                model=self._model,
                max_tokens=4096,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_message,
                    }
                ],
            ) as stream:
                async for text in stream.text_stream:
                    if text:
                        received_content = True
                        yield text

        except APITimeoutError as exc:
            raise ProviderTimeoutError(
                "Anthropic streaming request timed out.",
                provider="anthropic",
            ) from exc

        except APIConnectionError as exc:
            raise ProviderUnavailableError(
                "Anthropic is unavailable.",
                provider="anthropic",
            ) from exc

        except APIStatusError as exc:
            if exc.status_code >= 500:
                raise ProviderUnavailableError(
                    (
                        "Anthropic returned server error "
                        f"{exc.status_code}."
                    ),
                    provider="anthropic",
                ) from exc

            raise ProviderResponseError(
                (
                    "Anthropic returned HTTP "
                    f"{exc.status_code}."
                ),
                provider="anthropic",
            ) from exc

        except ProviderResponseError:
            raise

        except Exception as exc:
            raise ProviderResponseError(
                "Anthropic streaming request failed.",
                provider="anthropic",
            ) from exc

        if not received_content:
            raise ProviderResponseError(
                "Anthropic returned an empty response.",
                provider="anthropic",
            )