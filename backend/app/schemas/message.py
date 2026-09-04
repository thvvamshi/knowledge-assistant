from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MessageCreate(BaseModel):
    content: str = Field(
        min_length=1,
        max_length=10000,
    )
    provider: Literal["ollama", "anthropic"] | None = None


class SourceCitation(BaseModel):
    episode_title: str
    guest_name: str | None = None
    timestamp: str | None = None
    url: str | None = None


class ArtifactResponse(BaseModel):
    id: UUID
    type: str
    content: str
    created_at: datetime


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    role: str
    content: str
    provider: str | None = None
    model: str | None = None
    sources: list[SourceCitation] = Field(
        default_factory=list
    )
    artifact: ArtifactResponse | None = None
    created_at: datetime
