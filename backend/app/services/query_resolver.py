from __future__ import annotations

import re

from app.models.message import Message


_ARTIFACT_PREFIX_PATTERNS = (
    r"^\s*create\s+(?:a\s+)?markdown\s+artifact\s+(?:about|on|for|explaining|covering)\s+",
    r"^\s*generate\s+(?:a\s+)?markdown\s+artifact\s+(?:about|on|for|explaining|covering)\s+",
    r"^\s*write\s+(?:a\s+)?markdown\s+artifact\s+(?:about|on|for|explaining|covering)\s+",
    r"^\s*draft\s+(?:a\s+)?markdown\s+artifact\s+(?:about|on|for|explaining|covering)\s+",
    r"^\s*make\s+(?:a\s+)?markdown\s+artifact\s+(?:about|on|for|explaining|covering)\s+",
    r"^\s*create\s+(?:a\s+)?markdown\s+(?:about|on|for|explaining|covering)\s+",
    r"^\s*generate\s+(?:a\s+)?markdown\s+(?:about|on|for|explaining|covering)\s+",
    r"^\s*write\s+(?:a\s+)?markdown\s+(?:about|on|for|explaining|covering)\s+",
    r"^\s*draft\s+(?:a\s+)?markdown\s+(?:about|on|for|explaining|covering)\s+",
    r"^\s*make\s+(?:a\s+)?markdown\s+(?:about|on|for|explaining|covering)\s+",
)


def _is_follow_up_question(question: str) -> bool:
    text = question.strip().lower()

    if not text:
        return False

    follow_up_patterns = (
        r"^(can|could|would)\s+you\s+(elaborate|expand|explain)",
        r"^(can|could|would)\s+you\s+(say|tell)\s+more",
        r"^tell\s+me\s+more",
        r"^show\s+me\s+more",
        r"^what\s+about\s+(the\s+)?(?:first|second|third|fourth|fifth|last|next)\s+",
        r"^what\s+about\s+it\b",
        r"^what\s+about\s+that\b",
        r"^why\s*\??$",
        r"^how\s+so\s*\??$",
        r"^what\s+do\s+you\s+mean\s*\??$",
        r"^what\s+does\s+that\s+mean\s*\??$",
        r"^and\s+why\s*\??$",
        r"^and\s+what\s+about\b",
        r"^can\s+you\s+explain\s+that\b",
        r"^can\s+you\s+expand\s+on\s+that\b",
    )

    return any(
        re.search(pattern, text)
        for pattern in follow_up_patterns
    )


def _strip_artifact_instruction(question: str) -> str:
    """
    Remove the Markdown/artifact output instruction while preserving
    the actual knowledge topic used for transcript retrieval.
    """
    text = question.strip()

    for pattern in _ARTIFACT_PREFIX_PATTERNS:
        cleaned = re.sub(
            pattern,
            "",
            text,
            count=1,
            flags=re.IGNORECASE,
        )

        if cleaned != text:
            return cleaned.strip(" .:,-")

    return text


def _get_previous_context(
    conversation_history: list[Message],
) -> tuple[str | None, str | None]:
    """
    Get the most recent user question and assistant answer pair.
    """
    previous_user_question: str | None = None
    previous_assistant_answer: str | None = None

    for message in reversed(conversation_history):
        if (
            previous_assistant_answer is None
            and message.role == "assistant"
            and message.content.strip()
        ):
            previous_assistant_answer = message.content.strip()

        elif (
            previous_user_question is None
            and message.role == "user"
            and message.content.strip()
        ):
            previous_user_question = message.content.strip()

        if previous_user_question and previous_assistant_answer:
            break

    return previous_user_question, previous_assistant_answer


def build_retrieval_query(
    question: str,
    conversation_history: list[Message] | None = None,
) -> str:
    """
    Build a retrieval query while preserving the existing conversation
    follow-up behavior.

    Standalone questions:
        returned unchanged.

    Follow-up questions:
        include the previous user question and assistant answer.

    Markdown artifact requests:
        remove only the artifact-generation wrapper so retrieval focuses
        on the requested transcript topic.
    """
    question = question.strip()

    if not question:
        return ""

    history = conversation_history or []

    if not _is_follow_up_question(question):
        artifact_query = _strip_artifact_instruction(question)

        if artifact_query != question:
            return artifact_query

        return question

    previous_user_question, previous_assistant_answer = _get_previous_context(
        history
    )

    if not previous_user_question:
        return question

    current_query = _strip_artifact_instruction(question)

    parts = [
        f"Previous user question: {previous_user_question}",
    ]

    if previous_assistant_answer:
        parts.append(
            f"Previous assistant answer: {previous_assistant_answer}"
        )

    parts.append(
        f"Current user question: {current_query}"
    )

    return "\n".join(parts)
