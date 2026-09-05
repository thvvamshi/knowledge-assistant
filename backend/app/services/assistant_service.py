from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.assistant_agent import AssistantAgent
from app.models.message import Message
from app.providers.factory import get_llm_provider
from app.rag.context import (
    build_rag_context,
    format_source_citations,
)
from app.rag.retriever import retrieve_chunks
from app.services.artifact_service import ArtifactService
from app.services.query_resolver import (
    build_retrieval_query,
    is_conversational_query,
)


@dataclass
class AssistantResult:
    answer: str
    provider: str
    model: str
    sources: list[dict]
    artifact_content: str | None = None
    artifact_type: str | None = None
    artifact_title: str | None = None


def _format_history(
    messages: list[Message],
) -> str:
    if not messages:
        return "No previous conversation."

    lines: list[str] = []

    for message in messages:
        role = message.role.capitalize()

        lines.append(
            f"{role}: {message.content}"
        )

    return "\n".join(lines)


def response_provider_name(
    provider,
) -> str:
    value = getattr(
        provider,
        "provider_name",
        None,
    )

    if isinstance(value, str) and value.strip():
        return value

    class_name = (
        provider.__class__.__name__.lower()
    )

    if "ollama" in class_name:
        return "ollama"

    if "anthropic" in class_name:
        return "anthropic"

    if "fallback" in class_name:
        return "fallback"

    return class_name.replace(
        "provider",
        "",
    )


def response_model_name(
    provider,
) -> str:
    model = getattr(
        provider,
        "model",
        None,
    )

    if isinstance(model, str) and model.strip():
        return model

    return "unknown"


def _build_artifact_result(
    question: str,
    content: str,
):
    return ArtifactService.build_for_request(
        question,
        content,
    )


def _remove_source_number_tokens(
    answer: str,
) -> str:
    """
    Remove internal RAG source notation if the LLM
    leaks it into the answer.

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


def _remove_embedded_sources_section(
    answer: str,
) -> str:
    """
    Remove an LLM/backend-generated Sources section
    from the answer content.

    Sources are persisted separately in the structured
    `sources` field and rendered by the frontend.

    This prevents duplicate citations such as:

        answer
        ### Sources
        - ...

        Sources
        - ...

    The function handles Markdown-style source sections
    if an LLM happens to generate one.
    """

    if not answer.strip():
        return ""

    patterns = [
        r"\n\s*#{1,6}\s*Sources?\s*:?\s*\n[\s\S]*$",
        r"\n\s*#{1,6}\s*References?\s*:?\s*\n[\s\S]*$",
    ]

    cleaned = answer

    for pattern in patterns:
        cleaned = re.sub(
            pattern,
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

    return cleaned.strip()


def _normalize_answer(
    answer: str,
) -> str:
    """
    Normalize only the assistant answer.

    Source metadata is intentionally NOT appended here.

    The backend stores sources separately and the frontend
    renders them from Message.sources.
    """

    cleaned = _remove_source_number_tokens(
        answer
    )

    cleaned = _remove_embedded_sources_section(
        cleaned
    )

    return cleaned.strip()


async def _retrieve_context(
    session: AsyncSession,
    question: str,
    history: list[Message],
    top_k: int,
    similarity_threshold: float,
):
    """
    Retrieve transcript context only when the user
    message actually requires knowledge retrieval.

    Conversational messages such as "hi" or "thanks"
    intentionally bypass RAG.
    """

    retrieval_query = build_retrieval_query(
        question,
        history,
    )

    if not retrieval_query:
        return build_rag_context([])

    results = await retrieve_chunks(
        session,
        retrieval_query,
        top_k=top_k,
        similarity_threshold=similarity_threshold,
    )

    return build_rag_context(
        results
    )


async def answer_question(
    session: AsyncSession,
    question: str,
    conversation_history: list[Message] | None = None,
    provider_name: str | None = None,
    top_k: int = 5,
    similarity_threshold: float = 0.55,
) -> AssistantResult:
    history = (
        conversation_history
        or []
    )

    conversational = (
        is_conversational_query(
            question
        )
    )

    rag_context = await _retrieve_context(
        session=session,
        question=question,
        history=history,
        top_k=top_k,
        similarity_threshold=similarity_threshold,
    )

    # Knowledge questions require retrieved context.
    #
    # Conversational messages intentionally bypass RAG.
    if (
        not conversational
        and not rag_context.sources
    ):
        return AssistantResult(
            answer=(
                "I do not have sufficient "
                "information in the available "
                "knowledge base to answer this."
            ),
            provider="none",
            model="none",
            sources=[],
        )

    history_text = _format_history(
        history
    )

    provider = get_llm_provider(
        provider_name
    )

    agent = AssistantAgent(
        provider=provider
    )

    response = await agent.generate(
        question=question,
        rag_context=rag_context,
        history=history_text,
    )

    sources = format_source_citations(
        rag_context.sources
    )

    # Only normalize the answer itself.
    #
    # Sources remain structured metadata and are NOT
    # appended to the answer text.
    answer = _normalize_answer(
        response.content
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
        artifact_content=(
            artifact.content
            if artifact
            else None
        ),
        artifact_type=(
            artifact.artifact_type
            if artifact
            else None
        ),
        artifact_title=(
            artifact.title
            if artifact
            else None
        ),
    )


async def stream_question(
    session: AsyncSession,
    question: str,
    conversation_history: list[Message] | None = None,
    provider_name: str | None = None,
    top_k: int = 5,
    similarity_threshold: float = 0.55,
):
    history = (
        conversation_history
        or []
    )

    conversational = (
        is_conversational_query(
            question
        )
    )

    rag_context = await _retrieve_context(
        session=session,
        question=question,
        history=history,
        top_k=top_k,
        similarity_threshold=similarity_threshold,
    )

    # Knowledge questions without retrieved context
    # must remain grounded.
    if (
        not conversational
        and not rag_context.sources
    ):
        yield {
            "type": "complete",
            "answer": (
                "I do not have sufficient "
                "information in the available "
                "knowledge base to answer this."
            ),
            "provider": "none",
            "model": "none",
            "sources": [],
            "artifact": None,
        }

        return

    history_text = _format_history(
        history
    )

    provider = get_llm_provider(
        provider_name
    )

    agent = AssistantAgent(
        provider=provider
    )

    sources = format_source_citations(
        rag_context.sources
    )

    # Send structured source metadata separately.
    if sources:
        yield {
            "type": "sources",
            "sources": sources,
        }

    yield {
        "type": "metadata",
        "provider": response_provider_name(
            provider
        ),
        "model": response_model_name(
            provider
        ),
    }

    full_response: list[str] = []

    async for token in agent.stream(
        question=question,
        rag_context=rag_context,
        history=history_text,
    ):
        full_response.append(
            token
        )

        yield {
            "type": "token",
            "content": token,
        }

    raw_answer = "".join(
        full_response
    )

    # Keep persisted/complete answer clean.
    #
    # The source list is sent separately through the
    # `sources` event and the complete event.
    answer = _normalize_answer(
        raw_answer
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
            "provider": response_provider_name(
                provider
            ),
            "model": response_model_name(
                provider
            ),
            "sources": sources,
            "artifact": artifact_payload,
        }

        return

    yield {
        "type": "complete",
        "answer": answer,
        "provider": response_provider_name(
            provider
        ),
        "model": response_model_name(
            provider
        ),
        "sources": sources,
        "artifact": None,
    }


