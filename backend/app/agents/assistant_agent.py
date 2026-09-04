from dataclasses import dataclass
from typing import AsyncGenerator

from app.providers.base import LLMProvider
from app.rag.context import RAGContext
from app.skills.content_writing import (
    ContentWritingRequest,
    ContentWritingSkill,
)


@dataclass
class AgentResponse:
    content: str
    provider: str
    model: str


class AssistantAgent:
    """
    Application-level assistant agent.

    The agent owns conversation instructions, grounding rules, source
    attribution, and skill selection. LLM execution is delegated to the
    provider abstraction so the application can use Ollama locally and
    Anthropic as an optional fallback.
    """

    def __init__(self, provider: LLMProvider):
        self.provider = provider

    async def generate(
        self,
        question: str,
        rag_context: RAGContext,
        history: list[dict] | str | None = None,
    ) -> AgentResponse:
        if self._is_content_writing_request(question):
            return await self._generate_content(
                question=question,
                rag_context=rag_context,
                history=history,
            )

        system_prompt = self._build_system_prompt(
            rag_context=rag_context,
        )

        user_prompt = self._build_user_prompt(
            question=question,
            history=history,
        )

        response = await self.provider.generate(
            system_prompt=system_prompt,
            user_message=user_prompt,
        )

        return AgentResponse(
            content=self._clean_response(response.content),
            provider=response.provider,
            model=response.model,
        )

    async def stream(
        self,
        question: str,
        rag_context: RAGContext,
        history: list[dict] | str | None = None,
    ) -> AsyncGenerator[str, None]:
        if self._is_content_writing_request(question):
            async for token in self._stream_content(
                question=question,
                rag_context=rag_context,
                history=history,
            ):
                yield token

            return

        system_prompt = self._build_system_prompt(
            rag_context=rag_context,
        )

        user_prompt = self._build_user_prompt(
            question=question,
            history=history,
        )

        async for token in self.provider.stream(
            system_prompt=system_prompt,
            user_message=user_prompt,
        ):
            yield token

    async def _generate_content(
        self,
        question: str,
        rag_context: RAGContext,
        history: list[dict] | str | None = None,
    ) -> AgentResponse:
        history_text = self._format_history(history)

        request = ContentWritingRequest(
            topic=question,
            rag_context=rag_context,
            conversation_history=history_text,
        )

        skill = ContentWritingSkill()

        prompt = skill.build_prompt(request)

        response = await self.provider.generate(
            system_prompt=self._build_content_system_prompt(),
            user_message=prompt,
        )

        return AgentResponse(
            content=self._clean_response(response.content),
            provider=response.provider,
            model=response.model,
        )

    async def _stream_content(
        self,
        question: str,
        rag_context: RAGContext,
        history: list[dict] | str | None = None,
    ) -> AsyncGenerator[str, None]:
        history_text = self._format_history(history)

        request = ContentWritingRequest(
            topic=question,
            rag_context=rag_context,
            conversation_history=history_text,
        )

        skill = ContentWritingSkill()

        prompt = skill.build_prompt(request)

        async for token in self.provider.stream(
            system_prompt=self._build_content_system_prompt(),
            user_message=prompt,
        ):
            yield token

    def _build_system_prompt(
        self,
        rag_context: RAGContext,
    ) -> str:
        source_mapping = self._build_source_mapping(
            rag_context,
        )

        return f"""
You are a grounded podcast knowledge assistant.

Your job is to answer the user's question using ONLY the retrieved
transcript evidence supplied below.

GROUNDING RULES:

- Use only information supported by the supplied transcript excerpts.
- Do not invent facts, examples, statistics, names, recommendations,
  experiences, or opinions.
- Do not use outside knowledge to fill missing information.
- If the retrieved evidence is insufficient, explicitly say that the
  transcript knowledge base does not contain enough information to answer.
- You may combine evidence from multiple transcript excerpts when each
  individual claim is supported by the relevant source.
- Keep the answer conversational, useful, and directly relevant to the
  user's question.
- Preserve uncertainty when the transcript itself is uncertain.

SOURCE ATTRIBUTION:

The source mapping below is immutable and authoritative.

IMPORTANT:

- SOURCE N identifies exactly ONE transcript excerpt.
- You MUST NOT infer or guess that SOURCE N belongs to a different
  person, episode, or timestamp.
- A person mentioned in an excerpt is NOT automatically the speaker.
- Only attribute a statement to the guest when the transcript evidence
  explicitly supports that attribution.
- Never swap source metadata between sources.
- Never fabricate source metadata.
- Never modify an episode title, guest name, or timestamp.
- If a timestamp is unavailable, do not invent one.

Citation format:

[Episode: Guest Name, Timestamp/Topic]

If timestamp information is unavailable:

[Episode: Guest Name]

SOURCE MAPPING:

{source_mapping}

RETRIEVED TRANSCRIPT EVIDENCE:

{rag_context.context_text}
""".strip()

    def _build_content_system_prompt(self) -> str:
        return """
You are a transcript-grounded content-writing assistant.

You must follow the provided Ship30 content-writing skill exactly.

Use ONLY the transcript evidence supplied by the skill prompt.

Do not use outside knowledge.

Do not fabricate:
- facts
- statistics
- examples
- quotes
- people
- stories
- recommendations
- claims
- source metadata

Every substantive claim must be supported by the supplied transcript
evidence.

Use the exact source attribution information provided in the prompt.

If the evidence is insufficient, acknowledge the limitation rather than
inventing supporting material.

Return Markdown only.
""".strip()

    def _build_source_mapping(
        self,
        rag_context: RAGContext,
    ) -> str:
        if not rag_context.sources:
            return "No sources were retrieved."

        lines = []

        for index, source in enumerate(
            rag_context.sources,
            start=1,
        ):
            guest = source.guest_name or "Unknown guest"
            timestamp = source.timestamp or "Timestamp unavailable"

            lines.append(
                (
                    f"SOURCE {index}: "
                    f"Episode='{source.episode_title}'; "
                    f"Guest='{guest}'; "
                    f"Timestamp='{timestamp}'"
                )
            )

        return "\n".join(lines)

    def _build_user_prompt(
        self,
        question: str,
        history: list[dict] | str | None = None,
    ) -> str:
        history_text = self._format_history(history)

        return f"""
CONVERSATION HISTORY:

{history_text}

CURRENT USER QUESTION:

{question}

Answer the current question using the retrieved transcript evidence.
Maintain continuity with the conversation when relevant, but treat the
retrieved transcript evidence as the authoritative factual source.
""".strip()

    def _format_history(
        self,
        history: list[dict] | str | None,
    ) -> str:
        if history is None:
            return "No previous conversation."

        if isinstance(history, str):
            return history.strip() or "No previous conversation."

        if not history:
            return "No previous conversation."

        lines = []

        for message in history:
            if not isinstance(message, dict):
                continue

            role = message.get("role", "user")
            content = message.get("content", "")

            if content:
                lines.append(
                    f"{str(role).capitalize()}: {content}"
                )

        return "\n".join(lines) or "No previous conversation."

    @staticmethod
    def _is_content_writing_request(
        question: str,
    ) -> bool:
        normalized = question.lower()

        markers = (
            "write an article",
            "write a blog",
            "write a post",
            "create an article",
            "create a blog",
            "create a post",
            "ship30",
            "linkedin post",
            "blog post",
        )

        return any(
            marker in normalized
            for marker in markers
        )

    @staticmethod
    def _clean_response(
        content: str,
    ) -> str:
        return content.strip()