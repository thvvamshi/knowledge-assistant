from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.chunker import chunk_text
from app.ingestion.embedder import embed_texts
from app.ingestion.loader import find_transcripts
from app.ingestion.parser import parse_transcript
from app.models.transcript import TranscriptChunk


def build_transcript_chunks(
    source_path: Path,
) -> list[TranscriptChunk]:
    transcript = parse_transcript(source_path)

    chunks = chunk_text(transcript.content)

    if not chunks:
        return []

    embeddings = embed_texts(
        [chunk.content for chunk in chunks]
    )

    if len(chunks) != len(embeddings):
        raise ValueError(
            f"Embedding count mismatch for {source_path}: "
            f"{len(chunks)} chunks, {len(embeddings)} embeddings"
        )

    records: list[TranscriptChunk] = []

    for chunk, embedding in zip(chunks, embeddings):
        records.append(
            TranscriptChunk(
                episode_title=transcript.episode_title,
                guest_name=transcript.guest_name,
                episode_date=transcript.episode_date,
                timestamp=chunk.timestamp,
                topic=chunk.topic,
                source_path=transcript.source_path,
                youtube_url=transcript.youtube_url,
                video_id=transcript.video_id,
                content=chunk.content,
                chunk_index=chunk.chunk_index,
                embedding=embedding,
            )
        )

    return records


async def transcript_already_ingested(
    session: AsyncSession,
    source_path: str,
) -> bool:
    result = await session.execute(
        select(TranscriptChunk.id)
        .where(TranscriptChunk.source_path == source_path)
        .limit(1)
    )

    return result.scalar_one_or_none() is not None


async def ingest_transcripts(
    session: AsyncSession,
    source_dir: str,
) -> tuple[int, int, int]:
    transcript_files = find_transcripts(source_dir)

    total = len(transcript_files)

    transcripts_processed = 0
    chunks_inserted = 0
    transcripts_failed = 0

    print(f"Found {total} transcripts")
    print()

    for index, transcript_path in enumerate(
        transcript_files,
        start=1,
    ):
        source_path = str(transcript_path)

        try:
            if await transcript_already_ingested(
                session,
                source_path,
            ):
                print(
                    f"[{index}/{total}] SKIP "
                    f"{transcript_path.parent.name}"
                )
                continue

            records = build_transcript_chunks(
                transcript_path
            )

            if not records:
                print(
                    f"[{index}/{total}] EMPTY "
                    f"{transcript_path.parent.name}"
                )
                continue

            session.add_all(records)

            await session.commit()

            transcripts_processed += 1
            chunks_inserted += len(records)

            print(
                f"[{index}/{total}] OK "
                f"{transcript_path.parent.name} "
                f"({len(records)} chunks)"
            )

        except Exception as exc:
            await session.rollback()

            transcripts_failed += 1

            print(
                f"[{index}/{total}] FAILED "
                f"{transcript_path.parent.name}: {exc}"
            )

    print()
    print("Ingestion summary")
    print("-----------------")
    print(f"Total transcripts: {total}")
    print(f"Processed: {transcripts_processed}")
    print(f"Chunks inserted: {chunks_inserted}")
    print(f"Failed: {transcripts_failed}")

    return (
        transcripts_processed,
        chunks_inserted,
        transcripts_failed,
    )
