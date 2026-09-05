from collections.abc import AsyncGenerator

import httpx

from app.core.config import get_settings
from app.providers.base import LLMProvider, LLMResponse
from app.providers.exceptions import (
    ProviderConfigurationError,
    ProviderResponseError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)


class OpenRouterProvider(LLMProvider):
    """OpenRouter cloud LLM provider."""

    def __init__(self):
        settings = get_settings()

        self.base_url = settings.openrouter_base_url.rstrip("/")
        self._api_key = settings.openrouter_api_key
        self._model = settings.openrouter_model

        if not self.base_url:
            raise ProviderConfigurationError(
                "OpenRouter base URL is not configured.",
                provider="openrouter",
            )

        if not self._api_key:
            raise ProviderConfigurationError(
                "OpenRouter API key is not configured.",
                provider="openrouter",
            )

        if not self._model:
            raise ProviderConfigurationError(
                "OpenRouter model is not configured.",
                provider="openrouter",
            )

        self.timeout = httpx.Timeout(
            connect=10.0,
            read=300.0,
            write=30.0,
            pool=30.0,
        )

    @property
    def provider_name(self) -> str:
        return "openrouter"

    @property
    def model(self) -> str:
        return self._model

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "X-Title": "Lenny Growth Assistant",
        }

    def _payload(
        self,
        system_prompt: str,
        user_message: str,
        stream: bool,
    ) -> dict:
        return {
            "model": self._model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_message,
                },
            ],
            "stream": stream,
        }

    async def generate(
        self,
        system_prompt: str,
        user_message: str,
    ) -> LLMResponse:
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout
            ) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._headers(),
                    json=self._payload(
                        system_prompt,
                        user_message,
                        False,
                    ),
                )

                response.raise_for_status()

        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(
                "OpenRouter request timed out.",
                provider="openrouter",
            ) from exc

        except httpx.ConnectError as exc:
            raise ProviderUnavailableError(
                "OpenRouter is unavailable.",
                provider="openrouter",
            ) from exc

        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code

            if status_code == 429 or status_code >= 500:
                raise ProviderUnavailableError(
                    f"OpenRouter returned HTTP {status_code}.",
                    provider="openrouter",
                ) from exc

            raise ProviderResponseError(
                f"OpenRouter returned HTTP {status_code}.",
                provider="openrouter",
            ) from exc

        except httpx.HTTPError as exc:
            raise ProviderUnavailableError(
                "Unable to connect to OpenRouter.",
                provider="openrouter",
            ) from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise ProviderResponseError(
                "OpenRouter returned invalid JSON.",
                provider="openrouter",
            ) from exc

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderResponseError(
                "OpenRouter returned an unexpected response.",
                provider="openrouter",
            ) from exc

        if not isinstance(content, str) or not content.strip():
            raise ProviderResponseError(
                "OpenRouter returned an empty response.",
                provider="openrouter",
            )

        return LLMResponse(
            content=content.strip(),
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
            async with httpx.AsyncClient(
                timeout=self.timeout
            ) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers=self._headers(),
                    json=self._payload(
                        system_prompt,
                        user_message,
                        True,
                    ),
                ) as response:
                    try:
                        response.raise_for_status()
                    except httpx.HTTPStatusError as exc:
                        status_code = exc.response.status_code

                        if status_code == 429 or status_code >= 500:
                            raise ProviderUnavailableError(
                                f"OpenRouter returned HTTP {status_code}.",
                                provider="openrouter",
                            ) from exc

                        raise ProviderResponseError(
                            f"OpenRouter returned HTTP {status_code}.",
                            provider="openrouter",
                        ) from exc

                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue

                        if line == "data: [DONE]":
                            break

                        if not line.startswith("data:"):
                            continue

                        try:
                            data = httpx.Response(
                                200,
                                content=line[5:].strip(),
                            ).json()
                        except ValueError as exc:
                            raise ProviderResponseError(
                                "OpenRouter returned invalid streaming JSON.",
                                provider="openrouter",
                            ) from exc

                        choices = data.get("choices", [])

                        if not choices:
                            continue

                        delta = choices[0].get("delta", {})
                        token = delta.get("content", "")

                        if token:
                            received_content = True
                            yield token

        except ProviderResponseError:
            raise

        except ProviderUnavailableError:
            raise

        except ProviderTimeoutError:
            raise

        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(
                "OpenRouter streaming request timed out.",
                provider="openrouter",
            ) from exc

        except httpx.ConnectError as exc:
            raise ProviderUnavailableError(
                "OpenRouter is unavailable.",
                provider="openrouter",
            ) from exc

        except httpx.HTTPError as exc:
            raise ProviderUnavailableError(
                "Unable to connect to OpenRouter.",
                provider="openrouter",
            ) from exc

        if not received_content:
            raise ProviderResponseError(
                "OpenRouter returned an empty response.",
                provider="openrouter",
            )