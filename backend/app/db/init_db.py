from sqlalchemy import text

from app.db.base import Base
from app.db.session import engine
from app.models import Artifact, Message, Session, TranscriptChunk


async def init_db() -> None:
    async with engine.begin() as connection:
        await connection.execute(
            text("CREATE EXTENSION IF NOT EXISTS vector")
        )

        await connection.run_sync(Base.metadata.create_all)

        await connection.execute(
            text("""
                CREATE INDEX IF NOT EXISTS ix_transcript_chunks_embedding_hnsw
                ON transcript_chunks
                USING hnsw (embedding vector_cosine_ops)
            """)
        )

        await connection.execute(
            text("""
                CREATE INDEX IF NOT EXISTS transcript_chunks_content_fts_idx
                ON transcript_chunks
                USING GIN (to_tsvector('english', content))
            """)
        )
