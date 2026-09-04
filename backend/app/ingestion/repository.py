from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transcript import TranscriptChunk


async def transcript_exists(
    session: AsyncSession,
    source_path: str,
) -> bool:
    result = await session.execute(
        select(TranscriptChunk.id)
        .where(TranscriptChunk.source_path == source_path)
        .limit(1)
    )

    return result.scalar_one_or_none() is not None


async def insert_transcript_chunks(
    session: AsyncSession,
    chunks: list[TranscriptChunk],
) -> None:
    if not chunks:
        return

    session.add_all(chunks)
    await session.commit()
