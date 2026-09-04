from pathlib import Path


def find_transcripts(source_dir: str) -> list[Path]:
    root = Path(source_dir)

    if not root.exists():
        raise FileNotFoundError(
            f"Transcript source directory does not exist: {root}"
        )

    transcripts = sorted(root.rglob("transcript.md"))

    if not transcripts:
        raise FileNotFoundError(
            f"No transcript.md files found under: {root}"
        )

    return transcripts
