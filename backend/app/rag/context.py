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

    for index, result in enumerate(results, start=1):
        source_label = result.episode_title

        if result.guest_name:
            source_label += f" — {result.guest_name}"

        timestamp_line = ""

        if result.timestamp:
            timestamp_line = f"\nTimestamp: {result.timestamp}"

        url_line = ""

        if result.youtube_url:
            url_line = f"\nSource URL: {result.youtube_url}"

        sections.append(
            f"""SOURCE {index}
Episode: {source_label}{timestamp_line}{url_line}

Transcript excerpt:
{result.content}
"""
        )

    context_text = """The following information is retrieved from the transcript knowledge base.

GROUNDING RULES:
- Use only the transcript excerpts below to answer the user's question.
- Do not invent facts, examples, names, statistics, or recommendations that are not supported by these excerpts.
- If the excerpts do not contain enough information to answer the question, say that the transcript knowledge base does not contain enough information.
- When making a claim based on a source, cite it using [SOURCE N], where N is the source number.
- You may combine information from multiple sources when each claim is supported by the provided excerpts.

""" + "\n\n".join(sections)

    return RAGContext(
        context_text=context_text,
        sources=results,
    )


def format_source_citations(
    results: list[RetrievedChunk],
) -> list[dict]:
    citations: list[dict] = []

    for index, result in enumerate(results, start=1):
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