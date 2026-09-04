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


class OllamaProvider(LLMProvider):
    """Local Ollama LLM provider."""

    def __init__(self):
        settings = get_settings()

        self.base_url = settings.ollama_base_url.rstrip("/")
        self._model = settings.ollama_model

        if not self.base_url:
            raise ProviderConfigurationError(
                "Ollama base URL is not configured.",
                provider="ollama",
            )

        if not self._model:
            raise ProviderConfigurationError(
                "Ollama model is not configured.",
                provider="ollama",
            )

        self.timeout = httpx.Timeout(
            connect=10.0,
            read=300.0,
            write=30.0,
            pool=30.0,
        )

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def model(self) -> str:
        return self._model

    async def generate(
        self,
        system_prompt: str,
        user_message: str,
    ) -> LLMResponse:
        payload = {
            "model": self._model,
            "system": system_prompt,
            "prompt": user_message,
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout
            ) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                )

                response.raise_for_status()

        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(
                "Ollama request timed out.",
                provider="ollama",
            ) from exc

        except httpx.ConnectError as exc:
            raise ProviderUnavailableError(
                "Ollama is unavailable.",
                provider="ollama",
            ) from exc

        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code

            if status_code >= 500:
                raise ProviderUnavailableError(
                    (
                        "Ollama returned server error "
                        f"{status_code}."
                    ),
                    provider="ollama",
                ) from exc

            raise ProviderResponseError(
                f"Ollama returned HTTP {status_code}.",
                provider="ollama",
            ) from exc

        except httpx.HTTPError as exc:
            raise ProviderUnavailableError(
                "Unable to connect to Ollama.",
                provider="ollama",
            ) from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise ProviderResponseError(
                "Ollama returned invalid JSON.",
                provider="ollama",
            ) from exc

        content = data.get("response")

        if not isinstance(content, str) or not content.strip():
            raise ProviderResponseError(
                "Ollama returned an empty response.",
                provider="ollama",
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
        payload = {
            "model": self._model,
            "system": system_prompt,
            "prompt": user_message,
            "stream": True,
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout
            ) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json=payload,
                ) as response:
                    try:
                        response.raise_for_status()
                    except httpx.HTTPStatusError as exc:
                        status_code = exc.response.status_code

                        if status_code >= 500:
                            raise ProviderUnavailableError(
                                (
                                    "Ollama returned server error "
                                    f"{status_code}."
                                ),
                                provider="ollama",
                            ) from exc

                        raise ProviderResponseError(
                            (
                                "Ollama returned HTTP "
                                f"{status_code}."
                            ),
                            provider="ollama",
                        ) from exc

                    received_content = False

                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue

                        try:
                            data = httpx.Response(
                                200,
                                content=line,
                            ).json()
                        except ValueError as exc:
                            raise ProviderResponseError(
                                "Ollama returned invalid JSON.",
                                provider="ollama",
                            ) from exc

                        token = data.get("response", "")

                        if token:
                            received_content = True
                            yield token

                        if data.get("done") is True:
                            break

                    if not received_content:
                        raise ProviderResponseError(
                            "Ollama returned an empty response.",
                            provider="ollama",
                        )

        except ProviderResponseError:
            raise

        except ProviderUnavailableError:
            raise

        except ProviderTimeoutError:
            raise

        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(
                "Ollama streaming request timed out.",
                provider="ollama",
            ) from exc

        except httpx.ConnectError as exc:
            raise ProviderUnavailableError(
                "Ollama is unavailable.",
                provider="ollama",
            ) from exc

        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code

            if status_code >= 500:
                raise ProviderUnavailableError(
                    (
                        "Ollama returned server error "
                        f"{status_code}."
                    ),
                    provider="ollama",
                ) from exc

            raise ProviderResponseError(
                (
                    "Ollama returned HTTP "
                    f"{status_code}."
                ),
                provider="ollama",
            ) from exc

        except httpx.HTTPError as exc:
            raise ProviderUnavailableError(
                "Unable to connect to Ollama.",
                provider="ollama",
            ) from exc