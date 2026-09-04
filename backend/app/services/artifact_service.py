from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


ArtifactType = Literal["markdown"]


@dataclass
class ArtifactResult:
    content: str
    artifact_type: ArtifactType
    title: str


class ArtifactService:
    """Creates and normalizes artifacts produced by the assistant."""

    @staticmethod
    def is_artifact_request(question: str) -> bool:
        text = question.lower().strip()

        artifact_terms = (
            "create an artifact",
            "create artifact",
            "generate an artifact",
            "generate artifact",
            "write a markdown",
            "write markdown",
            "create markdown",
            "create a markdown",
            "generate markdown",
            "generate a markdown",
            "draft a markdown",
            "draft markdown",
            "make a markdown",
            "make markdown",
            "turn this into markdown",
            "convert this to markdown",
        )

        return any(term in text for term in artifact_terms)

    @staticmethod
    def clean_markdown(content: str) -> str:
        """Normalize model output while preserving Markdown."""
        if not content:
            return ""

        text = content.strip()

        # Remove accidental surrounding markdown fences.
        if text.startswith("```markdown") and text.endswith("```"):
            text = text[len("```markdown"):].strip()
            text = text[:-3].strip()
        elif text.startswith("```md") and text.endswith("```"):
            text = text[len("```md"):].strip()
            text = text[:-3].strip()

        return text

    @classmethod
    def build(
        cls,
        content: str,
        *,
        title: str = "Generated Artifact",
    ) -> ArtifactResult:
        markdown = cls.clean_markdown(content)

        return ArtifactResult(
            content=markdown,
            artifact_type="markdown",
            title=title,
        )
