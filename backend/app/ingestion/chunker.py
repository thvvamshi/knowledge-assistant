from dataclasses import dataclass
import re


@dataclass
class TranscriptChunkData:
    content: str
    chunk_index: int
    timestamp: str | None = None
    topic: str | None = None


DEFAULT_CHUNK_CHARACTERS = 3000
DEFAULT_OVERLAP_CHARACTERS = 400

TIMESTAMP_PATTERN = re.compile(
    r"\((\d{2}:\d{2}:\d{2})\)"
)


def extract_timestamp(text: str) -> str | None:
    match = TIMESTAMP_PATTERN.search(text)

    if match:
        return match.group(1)

    return None


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_CHARACTERS,
    overlap: int = DEFAULT_OVERLAP_CHARACTERS,
) -> list[TranscriptChunkData]:

    text = text.strip()

    if not text:
        return []

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    chunks: list[TranscriptChunkData] = []

    start = 0
    chunk_index = 0

    while start < len(text):
        end = min(
            start + chunk_size,
            len(text),
        )

        if end < len(text):
            boundary = text.rfind(
                "\n",
                start,
                end,
            )

            if boundary > start + (chunk_size // 2):
                end = boundary

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(
                TranscriptChunkData(
                    content=chunk,
                    chunk_index=chunk_index,
                    timestamp=extract_timestamp(chunk),
                )
            )

        if end >= len(text):
            break

        start = max(
            end - overlap,
            start + 1,
        )

        chunk_index += 1

    return chunks
