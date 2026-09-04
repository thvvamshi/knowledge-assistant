from app.core.config import get_settings
from app.providers.anthropic import AnthropicProvider
from app.providers.base import LLMProvider
from app.providers.fallback import FallbackLLMProvider
from app.providers.ollama import OllamaProvider


def _create_ollama_provider() -> OllamaProvider:
    return OllamaProvider()


def _create_anthropic_provider() -> AnthropicProvider | None:
    settings = get_settings()

    if not settings.anthropic_api_key:
        return None

    return AnthropicProvider()


def get_llm_provider(
    provider: str | None = None,
) -> LLMProvider:
    """
    Return an LLM provider based on the requested provider.

    Explicit provider selection:
        ollama    -> Ollama only
        anthropic -> Anthropic only

    Default selection:
        Ollama is preferred.
        Anthropic is used as a runtime fallback when configured.
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

    raise ValueError(
        f"Unsupported LLM provider: {selected_provider}"
    )


def get_default_llm_provider() -> LLMProvider:
    """
    Return the preferred provider configuration.

    Ollama is always preferred when configured.
    Anthropic becomes the fallback when an API key is available.
    """

    settings = get_settings()

    if settings.ollama_base_url:
        ollama = OllamaProvider()
        anthropic = _create_anthropic_provider()

        if anthropic is not None:
            return FallbackLLMProvider(
                primary=ollama,
                fallback=anthropic,
            )

        return ollama

    if settings.anthropic_api_key:
        return AnthropicProvider()

    raise RuntimeError(
        "No LLM provider is configured. "
        "Configure Ollama or provide ANTHROPIC_API_KEY."
    )