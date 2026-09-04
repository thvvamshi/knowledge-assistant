import asyncio

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.ingestion.pipeline import ingest_transcripts


async def main() -> None:
    settings = get_settings()

    async with AsyncSessionLocal() as session:
        transcripts, chunks, failed = await ingest_transcripts(
            session=session,
            source_dir=settings.transcript_source_dir,
        )

    print()
    print("Ingestion complete")
    print(f"Transcripts processed: {transcripts}")
    print(f"Chunks inserted: {chunks}")
    print(f"Transcripts failed: {failed}")


if __name__ == "__main__":
    asyncio.run(main())
