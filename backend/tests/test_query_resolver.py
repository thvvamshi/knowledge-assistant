from types import SimpleNamespace

from app.services.query_resolver import build_retrieval_query


def make_history():
    return [
        SimpleNamespace(
            role="user",
            content="What are some practical principles for product strategy?",
        ),
        SimpleNamespace(
            role="assistant",
            content=(
                "Use clear goals, understand users, "
                "and prioritize deliberately."
            ),
        ),
    ]


def test_standalone_question_is_not_rewritten():
    history = make_history()

    result = build_retrieval_query(
        "How do I launch a marketplace?",
        history,
    )

    assert result == "How do I launch a marketplace?"


def test_elaboration_follow_up_uses_previous_context():
    history = make_history()

    result = build_retrieval_query(
        "Can you elaborate?",
        history,
    )

    assert "Previous user question:" in result
    assert "Previous assistant answer:" in result
    assert "Can you elaborate?" in result


def test_reference_follow_up_uses_previous_context():
    history = make_history()

    result = build_retrieval_query(
        "What about the second point?",
        history,
    )

    assert "Previous user question:" in result
    assert "Previous assistant answer:" in result
    assert "What about the second point?" in result


def test_short_why_follow_up_uses_previous_context():
    history = make_history()

    result = build_retrieval_query(
        "Why?",
        history,
    )

    assert "Previous user question:" in result
    assert "Previous assistant answer:" in result
    assert "Why?" in result


def test_empty_question_returns_empty_string():
    result = build_retrieval_query("   ", make_history())

    assert result == ""