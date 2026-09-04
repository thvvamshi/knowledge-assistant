import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TranscriptChunk(Base):
    __tablename__ = "transcript_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    episode_title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
    )

    guest_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    episode_date: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    timestamp: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    topic: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    source_path: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
        index=True,
    )

    youtube_url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    video_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    embedding: Mapped[list[float]] = mapped_column(
        Vector(384),
        nullable=False,
    )

