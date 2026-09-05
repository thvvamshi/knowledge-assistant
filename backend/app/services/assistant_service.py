from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.assistant_agent import AssistantAgent
from app.models.message import Message
from app.providers.factory import get_llm_provider
from app.rag.context import build_rag_context, format_source_citations
from app.rag.retriever import retrieve_chunks
from app.services.artifact_service import ArtifactService
from app.services.query_resolver import build_retrieval_query


@dataclass
class AssistantResult:
    answer: str
    provider: str
    model: str
    sources: list[dict]
    artifact_content: str | None = None
    artifact_type: str | None = None
    artifact_title: str | None = None


def _format_history(messages: list[Message]) -> str:
    if not messages:
        return "No previous conversation."

    lines = []

    for message in messages:
        role = message.role.capitalize()
        lines.append(f"{role}: {message.content}")

    return "\n".join(lines)


def response_provider_name(provider) -> str:
    value = getattr(provider, "provider_name", None)

    if isinstance(value, str) and value.strip():
        return value

    class_name = provider.__class__.__name__.lower()

    if "ollama" in class_name:
        return "ollama"

    if "anthropic" in class_name:
        return "anthropic"

    if "fallback" in class_name:
        return "fallback"

    return class_name.replace("provider", "")


def response_model_name(provider) -> str:
    model = getattr(provider, "model", None)

    if isinstance(model, str) and model.strip():
        return model

    return "unknown"


def _build_artifact_result(question: str, content: str):
    if not ArtifactService.is_artifact_request(question):
        return None

    artifact = ArtifactService.build(
        content,
        title="Generated Markdown",
    )

    return artifact


def _citation_for_source(source: dict) -> str:
    episode_title = source.get("episode_title") or "Unknown episode"
    guest_name = source.get("guest_name") or "Unknown guest"
    timestamp = source.get("timestamp") or "Unknown timestamp"

    return (
        f"[Episode: {episode_title}, "
        f"Guest: {guest_name}, "
        f"Timestamp: {timestamp}]"
    )


def _build_sources_section(sources: list[dict]) -> str:
    if not sources:
        return ""

    lines = ["\n\n### Sources"]

    for source in sources:
        citation = _citation_for_source(source)
        url = source.get("url")

        if url:
            lines.append(f"- {citation} — {url}")
        else:
            lines.append(f"- {citation}")

    return "\n".join(lines)


def _remove_source_number_tokens(answer: str) -> str:
    """
    Remove internal RAG source notation if an LLM leaks it into the answer.

    Examples:
        [SOURCE 1]
        [SOURCE 2]
        [SOURCE 10]
    """
    return re.sub(
        r"\[SOURCE\s+\d+\]",
        "",
        answer,
        flags=re.IGNORECASE,
    )


def _normalize_answer(answer: str, sources: list[dict]) -> str:
    """
    Make source attribution deterministic.

    The LLM is responsible for writing the answer.
    The backend is responsible for exposing authoritative source metadata.

    This prevents hallucinated episode/guest/timestamp metadata and prevents
    internal SOURCE N identifiers from leaking to the user.
    """
    cleaned = _remove_source_number_tokens(answer).strip()

    sources_section = _build_sources_section(sources)

    if not sources_section:
        return cleaned

    return f"{cleaned}{sources_section}"


async def answer_question(
    session: AsyncSession,
    question: str,
    conversation_history: list[Message] | None = None,
    provider_name: str | None = None,
    top_k: int = 5,
    similarity_threshold: float = 0.55,
) -> AssistantResult:
    history = conversation_history or []

    retrieval_query = build_retrieval_query(
        question,
        history,
    )

    results = await retrieve_chunks(
        session,
        retrieval_query,
        top_k=top_k,
        similarity_threshold=similarity_threshold,
    )

    if not results:
        return AssistantResult(
            answer=(
                "I do not have sufficient information in the available "
                "knowledge base to answer this."
            ),
            provider="none",
            model="none",
            sources=[],
        )

    rag_context = build_rag_context(results)
    history_text = _format_history(history)

    provider = get_llm_provider(provider_name)
    agent = AssistantAgent(provider=provider)

    response = await agent.generate(
        question=question,
        rag_context=rag_context,
        history=history_text,
    )

    sources = format_source_citations(results)

    answer = _normalize_answer(
        response.content,
        sources,
    )

    artifact = _build_artifact_result(
        question,
        answer,
    )

    return AssistantResult(
        answer=answer,
        provider=response.provider,
        model=response.model,
        sources=sources,
        artifact_content=artifact.content if artifact else None,
        artifact_type=artifact.artifact_type if artifact else None,
        artifact_title=artifact.title if artifact else None,
    )


async def stream_question(
    session: AsyncSession,
    question: str,
    conversation_history: list[Message] | None = None,
    provider_name: str | None = None,
    top_k: int = 5,
    similarity_threshold: float = 0.55,
):
    history = conversation_history or []

    retrieval_query = build_retrieval_query(
        question,
        history,
    )

    results = await retrieve_chunks(
        session,
        retrieval_query,
        top_k=top_k,
        similarity_threshold=similarity_threshold,
    )

    if not results:
        yield {
            "type": "complete",
            "answer": (
                "I do not have sufficient information in the available "
                "knowledge base to answer this."
            ),
            "provider": "none",
            "model": "none",
            "sources": [],
            "artifact": None,
        }
        return

    rag_context = build_rag_context(results)
    history_text = _format_history(history)

    provider = get_llm_provider(provider_name)
    agent = AssistantAgent(provider=provider)

    sources = format_source_citations(results)

    yield {
        "type": "sources",
        "sources": sources,
    }

    yield {
        "type": "metadata",
        "provider": response_provider_name(provider),
        "model": response_model_name(provider),
    }

    full_response: list[str] = []

    async for token in agent.stream(
        question=question,
        rag_context=rag_context,
        history=history_text,
    ):
        full_response.append(token)

        yield {
            "type": "token",
            "content": token,
        }

    raw_answer = "".join(full_response)

    answer = _normalize_answer(
        raw_answer,
        sources,
    )

    artifact = _build_artifact_result(
        question,
        answer,
    )

    if artifact:
        artifact_payload = {
            "type": artifact.artifact_type,
            "title": artifact.title,
            "content": artifact.content,
        }

        yield {
            "type": "artifact",
            "artifact": artifact_payload,
        }

        yield {
            "type": "complete",
            "answer": answer,
            "provider": response_provider_name(provider),
            "model": response_model_name(provider),
            "sources": sources,
            "artifact": artifact_payload,
        }

        return

    yield {
        "type": "complete",
        "answer": answer,
        "provider": response_provider_name(provider),
        "model": response_model_name(provider),
        "sources": sources,
        "artifact": None,
    }

     