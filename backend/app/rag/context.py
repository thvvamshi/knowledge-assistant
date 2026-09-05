from dataclasses import dataclass

from app.rag.retriever import RetrievedChunk


@dataclass
class RAGContext:
    context_text: str
    sources: list[RetrievedChunk]


def build_rag_context(
    results: list[RetrievedChunk],
) -> RAGContext:
    if not results:
        return RAGContext(
            context_text="",
            sources=[],
        )

    sections: list[str] = []

    for index, result in enumerate(
        results,
        start=1,
    ):
        source_label = result.episode_title

        if result.guest_name:
            source_label += (
                f" — {result.guest_name}"
            )

        timestamp_line = ""

        if result.timestamp:
            timestamp_line = (
                f"\nTimestamp: {result.timestamp}"
            )

        url_line = ""

        if result.youtube_url:
            url_line = (
                f"\nSource URL: {result.youtube_url}"
            )

        sections.append(
            f"""SOURCE {index}
Episode: {source_label}{timestamp_line}{url_line}

Transcript excerpt:
{result.content}
"""
        )

    context_text = """The following information is retrieved from the transcript knowledge base.

GROUNDING RULES:
- Use only the transcript excerpts below to answer knowledge questions.
- Do not invent facts, examples, names, statistics, recommendations, or claims.
- Do not attribute information to a guest unless the transcript excerpt supports it.
- If the excerpts do not contain enough information to answer a knowledge question, say that the transcript knowledge base does not contain enough information.
- Source metadata is provided separately to the assistant.
- Do not expose SOURCE N identifiers in the final answer.

""" + "\n\n".join(sections)

    return RAGContext(
        context_text=context_text,
        sources=results,
    )


def format_source_citations(
    results: list[RetrievedChunk],
) -> list[dict]:
    citations: list[dict] = []

    for index, result in enumerate(
        results,
        start=1,
    ):
        citations.append(
            {
                "source_id": f"SOURCE {index}",
                "episode_title": result.episode_title,
                "guest_name": result.guest_name,
                "timestamp": result.timestamp,
                "url": result.youtube_url,
            }
        )

    return citations