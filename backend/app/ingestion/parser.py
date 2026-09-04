from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ParsedTranscript:
    source_path: str
    guest_name: str | None
    episode_title: str
    episode_date: str | None
    youtube_url: str | None
    video_id: str | None
    description: str | None
    content: str


def parse_transcript(path: Path) -> ParsedTranscript:
    raw = path.read_text(encoding="utf-8")

    metadata: dict[str, Any] = {}
    content = raw

    if raw.startswith("---"):
        parts = raw.split("---", 2)

        if len(parts) == 3:
            metadata = yaml.safe_load(parts[1]) or {}
            content = parts[2].strip()

    publish_date = metadata.get("publish_date")

    if publish_date is not None:
        publish_date = str(publish_date)

    youtube_url = metadata.get("youtube_url")

    if youtube_url is not None:
        youtube_url = str(youtube_url)

    return ParsedTranscript(
        source_path=str(path),
        guest_name=metadata.get("guest"),
        episode_title=metadata.get("title") or path.parent.name,
        episode_date=publish_date,
        youtube_url=youtube_url,
        video_id=metadata.get("video_id"),
        description=metadata.get("description"),
        content=content,
    )
