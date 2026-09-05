import httpx
from fastapi import APIRouter

from app.core.config import get_settings


router = APIRouter(
    prefix="/api/providers",
    tags=["providers"],
)


async def _check_ollama(
    base_url: str,
    model: str,
) -> bool:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{base_url.rstrip('/')}/api/tags"
            )
            response.raise_for_status()

            data = response.json()
            models = data.get("models", [])

            return any(
                item.get("name") == model
                for item in models
            )
    except (httpx.HTTPError, ValueError):
        return False


@router.get("")
async def get_providers():
    settings = get_settings()

    ollama_configured = bool(settings.ollama_base_url)
    anthropic_configured = bool(settings.anthropic_api_key)
    openrouter_configured = bool(settings.openrouter_api_key)

    ollama_available = False

    if ollama_configured:
        ollama_available = await _check_ollama(
            settings.ollama_base_url,
            settings.ollama_model,
        )

    return {
        "default_provider": settings.llm_provider.lower(),
        "providers": [
            {
                "id": "ollama",
                "name": "Ollama",
                "model": settings.ollama_model,
                "configured": ollama_configured,
                "available": ollama_available,
            },
            {
                "id": "anthropic",
                "name": "Anthropic",
                "model": settings.anthropic_model,
                "configured": anthropic_configured,
                "available": anthropic_configured,
            },
            {
                "id": "openrouter",
                "name": "OpenRouter",
                "model": settings.openrouter_model,
                "configured": openrouter_configured,
                "available": openrouter_configured,
            },
        ],
    }
