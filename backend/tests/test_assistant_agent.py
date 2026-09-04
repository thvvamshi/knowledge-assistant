from app.agents.assistant_agent import AssistantAgent


def test_article_request_is_detected_as_content_writing():
    assert AssistantAgent._is_content_writing_request(
        "Write an article about product strategy."
    )


def test_blog_request_is_detected_as_content_writing():
    assert AssistantAgent._is_content_writing_request(
        "Create a blog post about product growth."
    )


def test_normal_question_is_not_content_writing():
    assert not AssistantAgent._is_content_writing_request(
        "What are some practical principles for product strategy?"
    )


def test_marketplace_question_is_not_content_writing():
    assert not AssistantAgent._is_content_writing_request(
        "How do I launch a marketplace?"
    )