from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: UUID
    content: str = Field(
        min_length=1,
        max_length=10000,
    )

    provider: Literal["ollama", "anthropic"] | None = None

    top_k: int = Field(
        default=5,
        ge=1,
        le=10,
    )

    similarity_threshold: float = Field(
        default=0.55,
        ge=0.0,
        le=1.0,
    )

    generate_artifact: bool = False