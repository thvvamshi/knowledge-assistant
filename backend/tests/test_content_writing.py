from app.rag.context import RAGContext
from app.skills.content_writing import (
    ContentWritingRequest,
    ContentWritingSkill,
)


def _normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def _build_request(
    topic: str = "Write an article about product strategy.",
    context_text: str = (
        "SOURCE 1\n"
        "Episode: Product Strategy | Guest: Example Guest\n"
        "Timestamp: 00:10:00\n\n"
        "Transcript excerpt:\n"
        "Strategy starts with a clear problem and a focused customer."
    ),
    history: str = "No previous conversation.",
) -> ContentWritingRequest:
    return ContentWritingRequest(
        topic=topic,
        rag_context=RAGContext(
            context_text=context_text,
            sources=[],
        ),
        conversation_history=history,
    )


def test_content_writing_prompt_contains_topic():
    skill = ContentWritingSkill()

    prompt = skill.build_prompt(_build_request())

    assert "Write an article about product strategy." in prompt
    assert "Strategy starts with a clear problem" in prompt


def test_content_writing_prompt_requires_transcript_only_grounding():
    skill = ContentWritingSkill()

    prompt = _normalize_whitespace(
        skill.build_prompt(_build_request())
    )

    assert (
        "transcript context is the ONLY factual source available to you"
        in prompt
    )
    assert "Do not rely on general knowledge" in prompt
    assert (
        "Use ONLY information contained in the supplied transcript context."
        in prompt
    )
    assert "Do not fill the gap with outside knowledge." in prompt


def test_content_writing_prompt_targets_ship30_length():
    skill = ContentWritingSkill()

    prompt = skill.build_prompt(_build_request())

    assert "Target approximately 1250 words." in prompt
    assert "950–1500 words" in prompt


def test_content_writing_prompt_requires_ship30_structure():
    skill = ContentWritingSkill()

    prompt = _normalize_whitespace(
        skill.build_prompt(_build_request())
    )

    assert "A strong opening hook." in prompt
    assert "A clear narrative progression." in prompt
    assert "Use an H1 title." in prompt
    assert "Use descriptive H2 headings." in prompt
    assert "Keep paragraphs short" in prompt
    assert "Use **bold** selectively" in prompt
    assert "A useful ending." in prompt


def test_content_writing_prompt_requires_source_attribution():
    skill = ContentWritingSkill()

    prompt = _normalize_whitespace(
        skill.build_prompt(_build_request())
    )

    assert (
        "Every substantive claim derived from the transcript knowledge base"
        in prompt
    )
    assert "[Episode: Guest Name, Timestamp]" in prompt
    assert (
        "Use the exact episode title, guest name, and timestamp"
        in prompt
    )
    assert "Never invent or modify timestamps." in prompt
    assert "Never invent episode titles or guest names." in prompt


def test_content_writing_prompt_rejects_fabricated_evidence():
    skill = ContentWritingSkill()

    prompt = _normalize_whitespace(
        skill.build_prompt(_build_request())
    )

    assert "Do not invent statistics." in prompt
    assert "Do not invent examples." in prompt
    assert "Do not invent frameworks." in prompt
    assert "Do not invent quotes." in prompt
    assert "Do not fabricate citations." in prompt
    assert "Do not fabricate URLs." in prompt
    assert "Do not fabricate timestamps." in prompt


def test_content_writing_prompt_requires_actionable_takeaway():
    skill = ContentWritingSkill()

    prompt = _normalize_whitespace(
        skill.build_prompt(_build_request())
    )

    assert "practical takeaway" in prompt
    assert "actionable checklist" in prompt


def test_content_writing_prompt_includes_conversation_history():
    skill = ContentWritingSkill()

    prompt = skill.build_prompt(
        _build_request(
            history="User previously asked about product strategy."
        )
    )

    assert "User previously asked about product strategy." in prompt


def test_content_writing_prompt_separates_history_from_evidence():
    skill = ContentWritingSkill()

    prompt = _normalize_whitespace(
        skill.build_prompt(
            _build_request(
                history="The user believes prioritization is the main issue."
            )
        )
    )

    assert "Conversation history is NOT factual evidence." in prompt
    assert (
        "same claim is also supported by the supplied transcript context"
        in prompt
    )


def test_content_writing_prompt_handles_insufficient_context():
    skill = ContentWritingSkill()

    request = ContentWritingRequest(
        topic="Write an article about an unsupported topic.",
        rag_context=RAGContext(
            context_text="No relevant knowledge-base context was retrieved.",
            sources=[],
        ),
    )

    prompt = skill.build_prompt(request)

    assert "No relevant knowledge-base context was retrieved." in prompt
    assert (
        "transcript knowledge base does not contain enough information"
        in prompt
    )


def test_content_writing_prompt_requires_markdown_only_output():
    skill = ContentWritingSkill()

    prompt = _normalize_whitespace(
        skill.build_prompt(_build_request())
    )

    assert "Return ONLY the finished Markdown article." in prompt
    assert (
        "The final output must be a polished Markdown article"
        in prompt
    )