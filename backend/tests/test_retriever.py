import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.retriever import retrieve_chunks


@pytest.mark.anyio
async def test_retriever_returns_results_for_supported_query(
    db_session: AsyncSession,
):
    results = await retrieve_chunks(
        session=db_session,
        query="How should a product manager approach product strategy?",
        top_k=5,
    )

    assert len(results) > 0
    assert len(results) <= 5

    for result in results:
        assert result.episode_title
        assert result.content
        assert 0.0 <= result.similarity <= 1.0


@pytest.mark.anyio
async def test_retriever_returns_no_results_for_unsupported_query(
    db_session: AsyncSession,
):
    results = await retrieve_chunks(
        session=db_session,
        query="What is the history of the Roman Empire?",
        top_k=5,
    )

    assert results == [] 