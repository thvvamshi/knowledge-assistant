from app.core.config import get_settings
from app.providers.anthropic import AnthropicProvider
from app.providers.base import LLMProvider
from app.providers.fallback import FallbackLLMProvider
from app.providers.ollama import OllamaProvider
from app.providers.openrouter import OpenRouterProvider


def _create_ollama_provider() -> OllamaProvider:
    return OllamaProvider()


def _create_anthropic_provider() -> AnthropicProvider | None:
    settings = get_settings()

    if not settings.anthropic_api_key:
        return None

    return AnthropicProvider()


def _create_openrouter_provider() -> OpenRouterProvider | None:
    settings = get_settings()

    if not settings.openrouter_api_key:
        return None

    return OpenRouterProvider()


def get_llm_provider(
    provider: str | None = None,
) -> LLMProvider:
    """
    Return an LLM provider based on the requested provider.

    Explicit provider selection:
        ollama     -> Ollama, with Anthropic fallback when configured
        anthropic  -> Anthropic only
        openrouter -> OpenRouter only

    Default selection:
        Uses the configured LLM_PROVIDER.
    """

    settings = get_settings()

    selected_provider = (
        provider.lower().strip()
        if provider
        else settings.llm_provider.lower().strip()
    )

    if selected_provider == "ollama":
        ollama = _create_ollama_provider()
        anthropic = _create_anthropic_provider()

        if anthropic is not None:
            return FallbackLLMProvider(
                primary=ollama,
                fallback=anthropic,
            )

        return ollama

    if selected_provider == "anthropic":
        return AnthropicProvider()

    if selected_provider == "openrouter":
        openrouter = _create_openrouter_provider()

        if openrouter is None:
            raise ValueError(
                "OpenRouter is selected but OPENROUTER_API_KEY "
                "is not configured."
            )

        return openrouter

    raise ValueError(
        f"Unsupported LLM provider: {selected_provider}"
    )


def get_default_llm_provider() -> LLMProvider:
    """
    Return the configured default provider.

    The provider is selected through LLM_PROVIDER.
    """

    settings = get_settings()

    return get_llm_provider(settings.llm_provider)