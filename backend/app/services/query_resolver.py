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

    r"^\s*create\s+(?:an?\s+)?html(?:\s*/\s*css)?\s+(?:page\s+)?(?:about|on|for|explaining|covering)\s+",
    r"^\s*generate\s+(?:an?\s+)?html(?:\s*/\s*css)?\s+(?:page\s+)?(?:about|on|for|explaining|covering)\s+",
    r"^\s*write\s+(?:an?\s+)?html(?:\s*/\s*css)?\s+(?:page\s+)?(?:about|on|for|explaining|covering)\s+",
    r"^\s*build\s+(?:an?\s+)?html(?:\s*/\s*css)?\s+(?:page\s+)?(?:about|on|for|explaining|covering)\s+",

    r"^\s*create\s+(?:a\s+)?document\s+(?:about|on|for|explaining|covering)\s+",
    r"^\s*generate\s+(?:a\s+)?document\s+(?:about|on|for|explaining|covering)\s+",
    r"^\s*write\s+(?:a\s+)?document\s+(?:about|on|for|explaining|covering)\s+",
    r"^\s*draft\s+(?:a\s+)?document\s+(?:about|on|for|explaining|covering)\s+",

    r"^\s*create\s+(?:a\s+)?30\s*[-]?\s*for\s*[-]?\s*30\s+(?:essay\s+)?(?:about|on|for|explaining|covering)\s+",
    r"^\s*generate\s+(?:a\s+)?30\s*[-]?\s*for\s*[-]?\s*30\s+(?:essay\s+)?(?:about|on|for|explaining|covering)\s+",
    r"^\s*write\s+(?:a\s+)?30\s*[-]?\s*for\s*[-]?\s*30\s+(?:essay\s+)?(?:about|on|for|explaining|covering)\s+",
    r"^\s*draft\s+(?:a\s+)?30\s*[-]?\s*for\s*[-]?\s*30\s+(?:essay\s+)?(?:about|on|for|explaining|covering)\s+",
    r"^\s*make\s+(?:a\s+)?30\s*[-]?\s*for\s*[-]?\s*30\s+(?:essay\s+)?(?:about|on|for|explaining|covering)\s+",

    r"^\s*create\s+(?:a\s+)?ship30\s+(?:essay\s+)?(?:about|on|for|explaining|covering)\s+",
    r"^\s*generate\s+(?:a\s+)?ship30\s+(?:essay\s+)?(?:about|on|for|explaining|covering)\s+",
    r"^\s*write\s+(?:a\s+)?ship30\s+(?:essay\s+)?(?:about|on|for|explaining|covering)\s+",
    r"^\s*draft\s+(?:a\s+)?ship30\s+(?:essay\s+)?(?:about|on|for|explaining|covering)\s+",
)


_CONVERSATIONAL_EXACT_MATCHES = {
    "hi",
    "hi!",
    "hi.",
    "hello",
    "hello!",
    "hello.",
    "hey",
    "hey!",
    "hey.",
    "yo",
    "yo!",
    "thanks",
    "thanks!",
    "thank you",
    "thank you!",
    "thx",
    "ty",
    "good morning",
    "good morning!",
    "good afternoon",
    "good afternoon!",
    "good evening",
    "good evening.",
    "good evening!",
    "good night",
    "bye",
    "bye!",
    "goodbye",
    "goodbye!",
    "ok",
    "okay",
    "ok!",
    "okay!",
    "cool",
    "great",
    "nice",
    "awesome",
}


_CONVERSATIONAL_PATTERNS = (
    r"^how\s+are\s+you(?:\s+doing)?[?!.]?$",
    r"^how's\s+it\s+going[?!.]?$",
    r"^hows\s+it\s+going[?!.]?$",
    r"^what(?:'s| is)\s+up[?!.]?$",
    r"^are\s+you\s+there[?!.]?$",
    r"^can\s+you\s+hear\s+me[?!.]?$",
    r"^who\s+are\s+you[?!.]?$",
    r"^what\s+can\s+you\s+do[?!.]?$",
    r"^what\s+do\s+you\s+do[?!.]?$",
    r"^nice\s+to\s+meet\s+you[?!.]?$",
)


def is_conversational_query(
    question: str,
) -> bool:
    """
    Return True only when the message is clearly casual conversation.

    Conversational messages bypass transcript retrieval so that
    vector search cannot return an unrelated transcript.
    """

    text = " ".join(
        question.strip().lower().split()
    )

    if not text:
        return False

    if text in _CONVERSATIONAL_EXACT_MATCHES:
        return True

    return any(
        re.fullmatch(
            pattern,
            text,
            flags=re.IGNORECASE,
        )
        for pattern in _CONVERSATIONAL_PATTERNS
    )


def is_follow_up_question(
    question: str,
) -> bool:
    """
    Determine whether the current question depends on the previous
    conversation.
    """

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
        r"^why\s*[?!.]?$",
        r"^how\s+so\s*[?!.]?$",
        r"^what\s+do\s+you\s+mean\s*[?!.]?$",
        r"^what\s+does\s+that\s+mean\s*[?!.]?$",
        r"^and\s+why\s*[?!.]?$",
        r"^and\s+what\s+about\b",
        r"^can\s+you\s+explain\s+that\b",
        r"^can\s+you\s+expand\s+on\s+that\b",
    )

    return any(
        re.search(
            pattern,
            text,
        )
        for pattern in follow_up_patterns
    )


def _strip_artifact_instruction(
    question: str,
) -> str:
    """
    Remove the artifact/content-format instruction while preserving
    the actual knowledge topic used for transcript retrieval.

    Examples:

        Create a 30 for 30 essay about growth teams.
        -> growth teams

        Create an HTML page explaining growth loops.
        -> growth loops

        Create a markdown artifact about retention.
        -> retention
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
            return cleaned.strip(
                " .:,-"
            )

    return text


def _get_previous_context(
    conversation_history: list[Message],
) -> tuple[str | None, str | None]:
    """
    Get the most recent user question and assistant answer pair.
    """

    previous_user_question: str | None = None
    previous_assistant_answer: str | None = None

    for message in reversed(
        conversation_history
    ):
        if (
            previous_assistant_answer is None
            and message.role == "assistant"
            and message.content.strip()
        ):
            previous_assistant_answer = (
                message.content.strip()
            )

        elif (
            previous_user_question is None
            and message.role == "user"
            and message.content.strip()
        ):
            previous_user_question = (
                message.content.strip()
            )

        if (
            previous_user_question
            and previous_assistant_answer
        ):
            break

    return (
        previous_user_question,
        previous_assistant_answer,
    )


def build_retrieval_query(
    question: str,
    conversation_history: list[Message] | None = None,
) -> str:
    """
    Build the query used for transcript retrieval.

    Conversational messages:
        return an empty query so retrieval is skipped.

    Standalone questions:
        return the question unchanged unless it contains
        an artifact/content-writing wrapper.

    Follow-up questions:
        include relevant previous conversation context.

    Artifact requests:
        remove only the output-format instruction so retrieval
        focuses on the actual knowledge topic.
    """

    question = question.strip()

    if not question:
        return ""

    if is_conversational_query(question):
        return ""

    history = conversation_history or []

    current_query = _strip_artifact_instruction(
        question
    )

    if not is_follow_up_question(question):
        return current_query

    (
        previous_user_question,
        previous_assistant_answer,
    ) = _get_previous_context(
        history
    )

    if not previous_user_question:
        return current_query

    previous_query = _strip_artifact_instruction(
        previous_user_question
    )

    parts = [
        f"Previous user question: {previous_query}",
    ]

    if previous_assistant_answer:
        parts.append(
            "Previous assistant answer: "
            f"{previous_assistant_answer}"
        )

    parts.append(
        f"Current user question: {current_query}"
    )

    return "\n".join(parts)