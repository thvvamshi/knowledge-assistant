import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.services.assistant_service import answer_question


@pytest.mark.anyio
async def test_assistant_answers_grounded_question():
    settings = get_settings()

    test_engine = create_async_engine(
        settings.database_url,
        echo=False,
        pool_pre_ping=True,
        poolclass=NullPool,
    )

    TestSessionLocal = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    try:
        async with TestSessionLocal() as session:
            question = "How should a product manager approach product strategy?"

            result = await answer_question(
                session=session,
                question=question,
            )
    finally:
        await test_engine.dispose()

    assert result.answer
    assert result.provider
    assert result.model
    assert result.sources
