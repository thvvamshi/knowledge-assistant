import pytest
import httpx

from app.providers.exceptions import (
    ProviderConfigurationError,
    ProviderResponseError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)


def test_provider_exceptions_have_expected_hierarchy():
    from app.providers.exceptions import ProviderError

    assert issubclass(
        ProviderConfigurationError,
        ProviderError,
    )
    assert issubclass(
        ProviderUnavailableError,
        ProviderError,
    )
    assert issubclass(
        ProviderTimeoutError,
        ProviderError,
    )
    assert issubclass(
        ProviderResponseError,
        ProviderError,
    )


@pytest.mark.anyio
async def test_ollama_generate_maps_connection_error(monkeypatch):
    from app.providers.ollama import OllamaProvider

    async def mock_post(*args, **kwargs):
        raise httpx.ConnectError("connection refused")

    class MockClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        post = mock_post

    monkeypatch.setattr(
        "app.providers.ollama.httpx.AsyncClient",
        MockClient,
    )

    provider = OllamaProvider()

    with pytest.raises(ProviderUnavailableError):
        await provider.generate(
            "system",
            "hello",
        )


@pytest.mark.anyio
async def test_ollama_generate_maps_timeout(monkeypatch):
    from app.providers.ollama import OllamaProvider

    async def mock_post(*args, **kwargs):
        raise httpx.ReadTimeout("timeout")

    class MockClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        post = mock_post

    monkeypatch.setattr(
        "app.providers.ollama.httpx.AsyncClient",
        MockClient,
    )

    provider = OllamaProvider()

    with pytest.raises(ProviderTimeoutError):
        await provider.generate(
            "system",
            "hello",
        )


@pytest.mark.anyio
async def test_ollama_generate_rejects_invalid_json(monkeypatch):
    from app.providers.ollama import OllamaProvider

    class MockResponse:
        def raise_for_status(self):
            return None

        def json(self):
            raise ValueError("invalid json")

    async def mock_post(*args, **kwargs):
        return MockResponse()

    class MockClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        post = mock_post

    monkeypatch.setattr(
        "app.providers.ollama.httpx.AsyncClient",
        MockClient,
    )

    provider = OllamaProvider()

    with pytest.raises(ProviderResponseError):
        await provider.generate(
            "system",
            "hello",
        )


def test_anthropic_requires_api_key(monkeypatch):
    from app.providers.anthropic import AnthropicProvider

    monkeypatch.setattr(
        "app.providers.anthropic.get_settings",
        lambda: type(
            "Settings",
            (),
            {
                "anthropic_api_key": "",
                "anthropic_model": "test-model",
            },
        )(),
    )

    with pytest.raises(ProviderConfigurationError):
        AnthropicProvider()
