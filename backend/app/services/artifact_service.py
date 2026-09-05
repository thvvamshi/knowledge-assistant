from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


ArtifactType = Literal["markdown", "html"]


@dataclass
class ArtifactResult:
    content: str
    artifact_type: ArtifactType
    title: str


class ArtifactService:
    """Creates and normalizes artifacts produced by the assistant."""

    @staticmethod
    def is_artifact_request(question: str) -> bool:
        """
        Determine whether the user's request should produce
        a persisted artifact.
        """
        text = " ".join(
            question.lower().split()
        )

        artifact_terms = (
            "create an artifact",
            "create artifact",
            "generate an artifact",
            "generate artifact",
            "create a document",
            "create document",
            "generate a document",
            "generate document",
            "write a document",
            "write document",
            "create markdown",
            "create a markdown",
            "generate markdown",
            "generate a markdown",
            "write markdown",
            "write a markdown",
            "draft markdown",
            "draft a markdown",
            "make markdown",
            "make a markdown",
            "turn this into markdown",
            "convert this to markdown",
            "create html",
            "create an html",
            "create html/css",
            "create an html/css",
            "generate html",
            "generate an html",
            "generate html/css",
            "generate an html/css",
            "write html",
            "write an html",
            "write html/css",
            "write an html/css",
            "build an html page",
            "build html",
        )

        if any(
            term in text
            for term in artifact_terms
        ):
            return True

        if "30 for 30" in text:
            return True

        if "30-for-30" in text:
            return True

        if "ship30" in text:
            return True

        return False

    @staticmethod
    def detect_type(
        question: str,
    ) -> ArtifactType:
        """
        Determine the requested artifact format.

        Markdown remains the default because the 30 for 30
        workflow and existing artifact flow use Markdown.
        """
        text = " ".join(
            question.lower().split()
        )

        html_terms = (
            "html",
            "html/css",
            "html and css",
            "html + css",
            "web page",
            "webpage",
        )

        if any(
            term in text
            for term in html_terms
        ):
            return "html"

        return "markdown"

    @staticmethod
    def clean_markdown(
        content: str,
    ) -> str:
        """Normalize model output while preserving Markdown."""
        if not content:
            return ""

        text = content.strip()

        if (
            text.startswith("```markdown")
            and text.endswith("```")
        ):
            text = text[
                len("```markdown") :
            ].strip()

            text = text[:-3].strip()

        elif (
            text.startswith("```md")
            and text.endswith("```")
        ):
            text = text[
                len("```md") :
            ].strip()

            text = text[:-3].strip()

        return text

    @staticmethod
    def clean_html(
        content: str,
    ) -> str:
        """
        Normalize HTML artifact output.

        Removes accidental Markdown code fences while
        preserving the complete HTML document.
        """
        if not content:
            return ""

        text = content.strip()

        if text.startswith("```html"):
            text = text[
                len("```html") :
            ].strip()

            if text.endswith("```"):
                text = text[:-3].strip()

        elif text.startswith("```"):
            text = text[
                len("```") :
            ].strip()

            if text.endswith("```"):
                text = text[:-3].strip()

        return text

    @classmethod
    def build(
        cls,
        content: str,
        *,
        title: str = "Generated Artifact",
        artifact_type: ArtifactType = "markdown",
    ) -> ArtifactResult:
        """
        Build a normalized artifact.

        Markdown and HTML are supported. HTML is intentionally
        treated as untrusted content and is rendered through the
        frontend sandbox.
        """
        if artifact_type == "html":
            normalized = cls.clean_html(
                content
            )
        else:
            normalized = cls.clean_markdown(
                content
            )

        return ArtifactResult(
            content=normalized,
            artifact_type=artifact_type,
            title=title,
        )

    @classmethod
    def build_for_request(
        cls,
        question: str,
        content: str,
        *,
        title: str | None = None,
    ) -> ArtifactResult | None:
        """
        Build an artifact only when the user's request
        explicitly calls for one.
        """
        if not cls.is_artifact_request(
            question
        ):
            return None

        artifact_type = cls.detect_type(
            question
        )

        if title:
            artifact_title = title
        elif artifact_type == "html":
            artifact_title = "Generated HTML"
        else:
            artifact_title = "Generated Markdown"

        return cls.build(
            content,
            title=artifact_title,
            artifact_type=artifact_type,
        )