import pytest

from app.providers.base import LLMProvider, LLMResponse
from app.providers.exceptions import (
    ProviderConfigurationError,
    ProviderUnavailableError,
)
from app.providers.fallback import FallbackLLMProvider


class MockProvider(LLMProvider):
    def __init__(
        self,
        name: str,
        model_name: str,
        *,
        generate_error=None,
        stream_error=None,
        partial_stream_error=None,
    ):
        self._name = name
        self._model = model_name
        self.generate_error = generate_error
        self.stream_error = stream_error
        self.partial_stream_error = partial_stream_error
        self.stream_called = False

    @property
    def provider_name(self) -> str:
        return self._name

    @property
    def model(self) -> str:
        return self._model

    async def generate(
        self,
        system_prompt: str,
        user_message: str,
    ) -> LLMResponse:
        if self.generate_error:
            raise self.generate_error

        return LLMResponse(
            content=f"{self._name} response",
            provider=self._name,
            model=self._model,
        )

    async def stream(
        self,
        system_prompt: str,
        user_message: str,
    ):
        self.stream_called = True

        if self.stream_error:
            raise self.stream_error

        yield f"{self._name} "

        if self.partial_stream_error:
            raise self.partial_stream_error

        yield "response"


@pytest.mark.anyio
async def test_fallback_uses_primary_when_available():
    primary = MockProvider(
        "ollama",
        "gemma3:4b",
    )

    fallback = MockProvider(
        "anthropic",
        "claude-test",
    )

    provider = FallbackLLMProvider(
        primary=primary,
        fallback=fallback,
    )

    response = await provider.generate(
        "system",
        "hello",
    )

    assert response.content == "ollama response"
    assert response.provider == "ollama"
    assert response.model == "gemma3:4b"

    assert provider.provider_name == "ollama"
    assert provider.model == "gemma3:4b"


@pytest.mark.anyio
async def test_fallback_uses_secondary_when_primary_is_unavailable():
    primary = MockProvider(
        "ollama",
        "gemma3:4b",
        generate_error=ProviderUnavailableError(
            "Ollama unavailable",
            provider="ollama",
        ),
    )

    fallback = MockProvider(
        "anthropic",
        "claude-test",
    )

    provider = FallbackLLMProvider(
        primary=primary,
        fallback=fallback,
    )

    response = await provider.generate(
        "system",
        "hello",
    )

    assert response.content == "anthropic response"
    assert response.provider == "anthropic"
    assert response.model == "claude-test"

    assert provider.provider_name == "anthropic"
    assert provider.model == "claude-test"


@pytest.mark.anyio
async def test_fallback_does_not_hide_non_retryable_primary_errors():
    primary = MockProvider(
        "ollama",
        "gemma3:4b",
        generate_error=ProviderConfigurationError(
            "Ollama is not configured",
            provider="ollama",
        ),
    )

    fallback = MockProvider(
        "anthropic",
        "claude-test",
    )

    provider = FallbackLLMProvider(
        primary=primary,
        fallback=fallback,
    )

    with pytest.raises(ProviderConfigurationError):
        await provider.generate(
            "system",
            "hello",
        )


@pytest.mark.anyio
async def test_stream_fallback_uses_secondary_provider():
    primary = MockProvider(
        "ollama",
        "gemma3:4b",
        stream_error=ProviderUnavailableError(
            "Ollama unavailable",
            provider="ollama",
        ),
    )

    fallback = MockProvider(
        "anthropic",
        "claude-test",
    )

    provider = FallbackLLMProvider(
        primary=primary,
        fallback=fallback,
    )

    tokens = []

    async for token in provider.stream(
        "system",
        "hello",
    ):
        tokens.append(token)

    assert "".join(tokens) == "anthropic response"
    assert provider.provider_name == "anthropic"
    assert provider.model == "claude-test"


@pytest.mark.anyio
async def test_stream_does_not_fallback_after_partial_primary_output():
    primary = MockProvider(
        "ollama",
        "gemma3:4b",
        partial_stream_error=ProviderUnavailableError(
            "Ollama failed after partial output",
            provider="ollama",
        ),
    )

    fallback = MockProvider(
        "anthropic",
        "claude-test",
    )

    provider = FallbackLLMProvider(
        primary=primary,
        fallback=fallback,
    )

    tokens = []

    with pytest.raises(ProviderUnavailableError):
        async for token in provider.stream(
            "system",
            "hello",
        ):
            tokens.append(token)

    assert "".join(tokens) == "ollama "
    assert fallback.stream_called is False
    assert provider.provider_name == "ollama"
    assert provider.model == "gemma3:4b"


@pytest.mark.anyio
async def test_fallback_raises_when_both_providers_fail():
    primary = MockProvider(
        "ollama",
        "gemma3:4b",
        generate_error=ProviderUnavailableError(
            "Ollama unavailable",
            provider="ollama",
        ),
    )

    fallback = MockProvider(
        "anthropic",
        "claude-test",
        generate_error=ProviderUnavailableError(
            "Anthropic unavailable",
            provider="anthropic",
        ),
    )

    provider = FallbackLLMProvider(
        primary=primary,
        fallback=fallback,
    )

    with pytest.raises(ProviderUnavailableError) as exc_info:
        await provider.generate(
            "system",
            "hello",
        )

    assert "All configured LLM providers" in str(
        exc_info.value
    )
