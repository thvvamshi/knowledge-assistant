from __future__ import annotations

from dataclasses import dataclass

from langchain_core.messages import HumanMessage, SystemMessage

from app.providers.base import LLMProvider
from app.rag.context import RAGContext


CONTENT_WRITING_INSTRUCTIONS = """
CONTENT WRITING / SHIP30 MODE
-----------------------------
When the user asks for an article, post, newsletter, LinkedIn post, X post,
blog post, or other publishable content:

- Use the supplied transcript excerpts as the only factual source.
- Follow the requested format and audience.
- Start with a strong, useful hook.
- Use short paragraphs, headings, bullets, and bold anchors where appropriate.
- Make the result skimmable and practical.
- Include a concrete takeaway, checklist, framework, or actionable advice
  when supported by the transcript.
- Do not invent examples, statistics, quotes, names, claims, or conclusions.
- Clearly distinguish the guest's perspective from the assistant's framing.
- Attribute claims to the correct guest and episode.
- Every substantive transcript-grounded claim must have an exact source
  citation.
- Do not use [SOURCE 1], [SOURCE 2], etc. in the final answer.
"""


@dataclass
class AssistantAgent:
    provider: LLMProvider

    async def generate(
        self,
        question: str,
        rag_context: RAGContext,
        history: str = "",
    ):
        messages = self._build_messages(
            question=question,
            rag_context=rag_context,
            history=history,
        )

        response = await self.provider.generate(
            system_prompt=self._message_content(messages[0]),
            user_message=self._message_content(messages[1]),
        )

        return response

    async def stream(
        self,
        question: str,
        rag_context: RAGContext,
        history: str = "",
    ):
        messages = self._build_messages(
            question=question,
            rag_context=rag_context,
            history=history,
        )

        async for token in self.provider.stream(
            system_prompt=self._message_content(messages[0]),
            user_message=self._message_content(messages[1]),
        ):
            yield token

    def _build_messages(
        self,
        question: str,
        rag_context: RAGContext,
        history: str,
    ) -> list:
        source_mapping = self._build_source_mapping(rag_context)

        system_prompt = """
You are a grounded knowledge assistant.

Your answers must be based ONLY on the transcript excerpts supplied in the
retrieved knowledge context.

Do not use outside knowledge to answer the user's question.

GROUNDING RULES
---------------
- Never invent facts.
- Never invent names.
- Never invent statistics.
- Never invent examples.
- Never invent episode titles.
- Never invent guest names.
- Never invent timestamps.
- Never invent source URLs.
- Do not attribute a claim to a person unless the supplied transcript excerpt
  supports that attribution.
- If the retrieved excerpts do not contain enough information, say:
  "I do not have sufficient information in the available knowledge base to
  answer this."

CITATION RULES
--------------
Every substantive claim derived from a transcript must include a citation.

Use EXACTLY this format:

[Episode: EXACT EPISODE TITLE, Guest: EXACT GUEST NAME, Timestamp: EXACT TIMESTAMP]

The episode title, guest name, and timestamp MUST be copied exactly from the
SOURCE METADATA.

Do NOT output:
- [SOURCE 1]
- [SOURCE 2]
- [SOURCE N]
- source numbers as citations
- invented citation metadata
- shortened or modified episode titles
- shortened or modified guest names
- approximate timestamps

SOURCE MAPPING IS IMMUTABLE
---------------------------
Each SOURCE number has one fixed metadata record.

For example, if SOURCE 4 contains:

Episode: The original growth hacker reveals his secrets
Guest: Sean Ellis
Timestamp: 00:01:58

then SOURCE 4 may only be represented using that exact metadata.

Never combine the episode title from one source with the guest or timestamp
from another source.

ATTRIBUTION RULES
-----------------
When a transcript excerpt supports a claim made by a specific guest, identify
that guest correctly.

Do not say "Lenny says" simply because the conversation appears on Lenny's
podcast.

Lenny is the host unless the retrieved transcript explicitly establishes that
Lenny is the speaker making the claim.

If the source metadata identifies the guest as Sean Ellis, do not attribute
that source's claim to another guest.

ANSWER QUALITY
--------------
- Answer the user's actual question directly.
- Prefer concise, useful explanations.
- Do not mention internal retrieval mechanics.
- Do not mention SOURCE numbers in the final answer.
- Do not fabricate information to make the answer more complete.
- When multiple sources support different claims, cite each claim with the
  correct source.
""".strip()

        if self._is_content_writing_request(question):
            system_prompt += "\n\n" + CONTENT_WRITING_INSTRUCTIONS.strip()

        user_prompt = f"""
QUESTION
--------
{question}

CONVERSATION HISTORY
--------------------
{history or "No previous conversation."}

RETRIEVED TRANSCRIPT KNOWLEDGE
------------------------------
{rag_context.context_text}

SOURCE METADATA
---------------
{source_mapping}

FINAL INSTRUCTION
-----------------
Answer the question using only the retrieved transcript knowledge.

Before producing the answer:

1. Check that every factual claim is supported by a retrieved excerpt.
2. Check that every guest attribution matches the actual source.
3. Check that every citation uses the exact episode title, guest name, and
   timestamp from SOURCE METADATA.
4. Never output [SOURCE N] notation.
5. If a claim cannot be supported, remove it rather than guessing.
""".strip()

        return [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

    @staticmethod
    def _build_source_mapping(rag_context: RAGContext) -> str:
        if not rag_context.sources:
            return "No source metadata available."

        lines: list[str] = []

        for index, source in enumerate(rag_context.sources, start=1):
            lines.append(
                f"SOURCE {index}\n"
                f"Episode: {source.episode_title}\n"
                f"Guest: {source.guest_name or 'Unknown'}\n"
                f"Timestamp: {source.timestamp or 'Unknown'}\n"
                f"URL: {source.youtube_url or 'Unknown'}"
            )

        return "\n\n".join(lines)

    @staticmethod
    def _is_content_writing_request(question: str) -> bool:
        normalized = question.lower()

        phrases = (
            "write",
            "draft",
            "article",
            "post",
            "newsletter",
            "linkedin",
            "linkedin post",
            "twitter",
            "x post",
            "blog",
            "ship30",
            "content",
            "thread",
        )

        return any(phrase in normalized for phrase in phrases)

    @staticmethod
    def _message_content(message) -> str:
        content = message.content

        if isinstance(content, str):
            return content

        return str(content)