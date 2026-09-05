from __future__ import annotations

from dataclasses import dataclass

from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
)

from app.providers.base import LLMProvider
from app.rag.context import RAGContext
from app.services.query_resolver import (
    is_conversational_query,
)


CONTENT_WRITING_INSTRUCTIONS = """
CONTENT WRITING MODE
--------------------
When the user asks for an article, post, newsletter, LinkedIn post,
X post, blog post, or other publishable content:

- Use the supplied transcript excerpts as the only factual source.
- Follow the requested format and audience.
- Start with a strong, useful hook.
- Use short paragraphs, headings, bullets, and bold anchors where appropriate.
- Make the result skimmable and practical.
- Make the writing feel like a coherent piece of content, not a transcript
  summary or a list of interview notes.
- Include a concrete takeaway, checklist, framework, or actionable advice
  when supported by the transcript.
- Do not invent examples, statistics, quotes, names, claims, or conclusions.
- Clearly distinguish the guest's perspective from the assistant's framing.
- Attribute claims to the correct guest and episode.
- Every substantive transcript-grounded claim must have an exact source
  citation.
- Do not use [SOURCE 1], [SOURCE 2], etc. in the final answer.
- Do not add a Sources or References section because sources are rendered
  separately by the application.
""".strip()


SHIP30_SYSTEM_PROMPT = """
30 FOR 30 / SHIP30 MODE
-----------------------
Create a polished, publishable 30 for 30 essay.

The goal is NOT to summarize every retrieved transcript.

The goal is to identify one strong central idea from the available evidence
and turn it into a coherent essay that teaches the reader something useful.

LENGTH
------
- Aim for approximately 1,250 words for the essay body.
- The target is approximately 1,250 words, not a hard requirement.
- If the available evidence cannot support a longer essay, prioritize accuracy
  over length.
- Never pad the essay with generic advice or unsupported claims.

NARRATIVE
---------
Build the essay around ONE central thesis.

Prefer this progression:

1. HOOK
   Open with a concrete tension, surprising observation, important problem,
   or useful insight supported by the transcripts.

2. PROBLEM
   Explain why the problem matters using the available evidence.

3. INSIGHT
   Introduce the strongest relevant idea from the guests.

4. DEVELOPMENT
   Develop that idea through the most relevant supporting evidence.
   Use other guests only when their perspectives genuinely strengthen,
   contrast with, or extend the central idea.

5. PRACTICAL IMPLICATION
   Explain what the reader should do differently based on the evidence.

6. CONCLUSION
   Return to the central idea and leave the reader with a clear,
   memorable takeaway.

Do NOT structure the essay as:
- Guest 1 said...
- Guest 2 said...
- Guest 3 said...

Avoid turning the essay into a collection of interview summaries.

SOURCE SELECTION
----------------
Use the most relevant transcript evidence.

Do not force every retrieved source into the essay.

It is better to deeply develop three relevant sources than to mention five
sources superficially.

VOICE
-----
- Write for an intelligent professional reader.
- Be clear, direct, practical, and engaging.
- Sound like a thoughtful human essay, not a research report.
- Avoid generic motivational language.
- Avoid repetitive phrases such as "this highlights the importance of".
- Avoid unnecessary introductions and conclusions.
- Prefer concrete explanations over abstract statements.
- Use descriptive headings that advance the argument.
- Keep paragraphs relatively short.
- Use bullets or numbered lists only when they genuinely improve readability.

QUOTES
-------
Only use a direct quote when the supplied transcript evidence explicitly
contains the quote.

Never invent or reconstruct a quote.

When a quote is not necessary, prefer accurate paraphrasing.

GROUNDING
---------
The supplied transcript excerpts are the ONLY factual source.

Do not use outside knowledge.

Do not invent:
- statistics
- examples
- quotes
- names
- companies
- product details
- frameworks
- conclusions
- guest opinions
- episode details

If the transcript evidence is insufficient for a requested point, omit the
point rather than guessing.

ATTRIBUTION
-----------
Clearly distinguish between:
1. what a guest actually said or argued in the transcript, and
2. the assistant's framing or synthesis.

Attribute claims to the correct guest.

Do not attribute a claim to Lenny merely because it appeared on Lenny's
podcast.

CITATIONS
---------
Every substantive transcript-grounded claim must include an exact citation.

Use exactly this format:

[Episode: EXACT EPISODE TITLE, Guest: EXACT GUEST NAME, Timestamp: EXACT TIMESTAMP]

Copy the episode title, guest name, and timestamp exactly from SOURCE METADATA.

If guest metadata is unavailable, use:
Unknown

If timestamp metadata is unavailable, use:
Unknown

Never use:
- [SOURCE 1]
- [SOURCE 2]
- [SOURCE N]
- approximate timestamps
- shortened episode titles
- modified guest names
- invented URLs

SOURCE MAPPING IS IMMUTABLE
---------------------------
Each SOURCE number maps to exactly one metadata record.

Never combine metadata from different sources.

For example:

SOURCE 2
Episode: Example episode
Guest: Example Guest
Timestamp: 00:12:34

must always produce:

[Episode: Example episode, Guest: Example Guest, Timestamp: 00:12:34]

Do not mix that episode title with metadata from another source.

FINAL QUALITY CHECK
-------------------
Before returning the essay:

1. Confirm there is one clear central thesis.
2. Confirm the opening is a strong hook.
3. Confirm the essay develops an argument rather than summarizing sources.
4. Confirm the most relevant evidence is prioritized.
5. Remove unsupported factual claims.
6. Check every guest attribution.
7. Check every direct quote against the supplied transcript evidence.
8. Check every citation against SOURCE METADATA.
9. Never output SOURCE-number notation.
10. Do not add a Sources or References section.
11. Do not mention retrieval, RAG, system prompts, or internal processing.
""".strip()


HTML_ARTIFACT_SYSTEM_PROMPT = """
HTML ARTIFACT MODE
------------------
The user is asking for an HTML artifact.

Return a COMPLETE, SELF-CONTAINED HTML DOCUMENT that can be rendered directly
inside a sandboxed iframe.

OUTPUT FORMAT
-------------
Return ONLY valid HTML.

Start with:
<!DOCTYPE html>

Include:
- <html>
- <head>
- <meta charset="UTF-8">
- <meta name="viewport" content="width=device-width, initial-scale=1.0">
- <title>
- a <style> block
- <body>

Do NOT wrap the HTML in Markdown code fences.

Do NOT write an explanation before or after the HTML.

DESIGN
------
Create a polished, modern, responsive page.

Use:
- clear visual hierarchy
- readable typography
- useful spacing
- cards or sections when appropriate
- responsive layouts
- accessible semantic HTML
- buttons or interactive elements only when they provide useful value

Keep the design self-contained.

Do not depend on external JavaScript libraries, CSS frameworks, fonts,
images, APIs, or network requests.

Do not use external resources that may fail inside the sandbox.

GROUNDING
---------
The supplied transcript excerpts are the ONLY factual source for the
content of the page.

Do not use outside knowledge.

Do not invent:
- statistics
- examples
- quotes
- names
- companies
- product details
- claims
- conclusions

If the retrieved evidence does not support a detail, omit it.

CITATIONS
---------
When the page makes substantive claims derived from the transcript, include
the exact citation metadata in visible text using:

[Episode: EXACT EPISODE TITLE, Guest: EXACT GUEST NAME, Timestamp: EXACT TIMESTAMP]

Copy episode title, guest name, and timestamp exactly from SOURCE METADATA.

Never use:
- [SOURCE 1]
- [SOURCE 2]
- [SOURCE N]
- invented timestamps
- invented episode titles
- invented guest names

Do not create a separate Sources or References section unless the user
explicitly requests one. The application already displays source metadata
separately.

SECURITY
--------
The generated document will be sanitized and rendered in a sandboxed iframe.

Do not include:
- external scripts
- iframes
- object
- embed
- meta refresh
- forms that submit to external URLs
- event-handler attributes such as onclick
- network calls
- tracking code

JAVASCRIPT
----------
Prefer no JavaScript.

If a small interaction materially improves the requested artifact, use only
small self-contained JavaScript inside the document and do not access the
parent page, cookies, storage, or external resources.

FINAL QUALITY CHECK
-------------------
Before returning:

1. Confirm the output begins with <!DOCTYPE html>.
2. Confirm it is a complete HTML document.
3. Confirm CSS is included.
4. Confirm the page is useful without external resources.
5. Confirm factual content is grounded in the supplied transcripts.
6. Confirm citations use exact SOURCE METADATA.
7. Remove Markdown code fences.
8. Do not include explanatory prose outside the HTML document.
""".strip()


CONVERSATIONAL_SYSTEM_PROMPT = """
You are a helpful conversational assistant.

The user's message is casual conversation rather than a request for
information from the transcript knowledge base.

Respond naturally, briefly, and helpfully.

If the user is greeting you, greet them back.

If the user is thanking you, respond naturally.

If the user asks what you can do, briefly explain that you can answer
questions using the available podcast knowledge base and help create
grounded written artifacts.

Do not invent podcast facts.

Do not introduce unrelated transcript information.

Do not mention retrieval, RAG, sources, or internal system behavior.
""".strip()


GROUNDED_SYSTEM_PROMPT = """
You are a grounded knowledge assistant.

Your answers to knowledge questions must be based ONLY on the transcript
excerpts supplied in the retrieved knowledge context.

Do not use outside knowledge to answer the user's knowledge question.

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

If guest metadata is unavailable, use the exact value "Unknown".

If timestamp metadata is unavailable, use the exact value "Unknown".

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
When a transcript excerpt supports a claim made by a specific guest,
identify that guest correctly.

Do not say "Lenny says" simply because the conversation appears on Lenny's
podcast.

Lenny is the host unless the retrieved transcript explicitly establishes
that Lenny is the speaker making the claim.

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
- Do not add a Sources or References section because the application renders
  structured sources separately.
""".strip()


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

        return await self.provider.generate(
            system_prompt=self._message_content(
                messages[0]
            ),
            user_message=self._message_content(
                messages[1]
            ),
        )

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
            system_prompt=self._message_content(
                messages[0]
            ),
            user_message=self._message_content(
                messages[1]
            ),
        ):
            yield token

    def _build_messages(
        self,
        question: str,
        rag_context: RAGContext,
        history: str,
    ) -> list:
        if is_conversational_query(question):
            return self._build_conversational_messages(
                question=question,
                history=history,
            )

        if self._is_ship30_request(question):
            return self._build_ship30_messages(
                question=question,
                rag_context=rag_context,
                history=history,
            )

        if self._is_html_artifact_request(question):
            return self._build_html_artifact_messages(
                question=question,
                rag_context=rag_context,
                history=history,
            )

        return self._build_grounded_messages(
            question=question,
            rag_context=rag_context,
            history=history,
        )

    @staticmethod
    def _build_conversational_messages(
        question: str,
        history: str,
    ) -> list:
        user_prompt = f"""
USER MESSAGE
------------
{question}

CONVERSATION HISTORY
--------------------
{history or "No previous conversation."}

FINAL INSTRUCTION
-----------------
Respond naturally to the user's message.

Keep the response concise.

Do not bring unrelated podcast transcript information into the response.
""".strip()

        return [
            SystemMessage(
                content=CONVERSATIONAL_SYSTEM_PROMPT,
            ),
            HumanMessage(
                content=user_prompt,
            ),
        ]

    def _build_ship30_messages(
        self,
        question: str,
        rag_context: RAGContext,
        history: str,
    ) -> list:
        source_mapping = self._build_source_mapping(
            rag_context
        )

        user_prompt = f"""
USER REQUEST
------------
{question}

CONVERSATION HISTORY
--------------------
{history or "No previous conversation."}

RETRIEVED TRANSCRIPT KNOWLEDGE
------------------------------
{rag_context.context_text or "No transcript knowledge was retrieved."}

SOURCE METADATA
---------------
{source_mapping}

FINAL INSTRUCTION
-----------------
Create the requested 30 for 30 essay.

First identify the strongest single idea supported by the retrieved
transcripts.

Then build the entire essay around that idea.

Do NOT attempt to summarize every source.

Prefer the strongest and most relevant evidence over broad source coverage.

The essay should:

- open with a compelling hook
- establish a clear tension or problem
- develop one central thesis
- use evidence from the most relevant guests
- connect the evidence into one coherent narrative
- explain why the insight matters
- give practical implications when supported
- end with a memorable conclusion

Aim for approximately 1,250 words when the evidence supports it.

Do not pad the essay with generic advice.

Use exact citations for substantive transcript-grounded claims.

Do not output [SOURCE N] notation.

Do not create a Sources or References section.

Do not use outside knowledge.
""".strip()

        return [
            SystemMessage(
                content=(
                    GROUNDED_SYSTEM_PROMPT
                    + "\n\n"
                    + SHIP30_SYSTEM_PROMPT
                ),
            ),
            HumanMessage(
                content=user_prompt,
            ),
        ]

    def _build_html_artifact_messages(
        self,
        question: str,
        rag_context: RAGContext,
        history: str,
    ) -> list:
        source_mapping = self._build_source_mapping(
            rag_context
        )

        user_prompt = f"""
USER REQUEST
------------
{question}

CONVERSATION HISTORY
--------------------
{history or "No previous conversation."}

RETRIEVED TRANSCRIPT KNOWLEDGE
------------------------------
{rag_context.context_text or "No transcript knowledge was retrieved."}

SOURCE METADATA
---------------
{source_mapping}

FINAL INSTRUCTION
-----------------
Create the requested HTML artifact.

Return ONLY the complete HTML document.

The output MUST:

- begin with <!DOCTYPE html>
- contain <html>, <head>, and <body>
- contain a <title>
- contain responsive CSS inside a <style> block
- be visually polished and easy to read
- work without external resources
- use semantic HTML
- be useful as a standalone page
- use only information supported by the retrieved transcripts
- include exact citations for substantive transcript-grounded claims

Do not return Markdown.

Do not use ```html or ```.

Do not explain the HTML before or after the document.

Do not add a Sources or References section.

Do not use outside knowledge.
""".strip()

        return [
            SystemMessage(
                content=(
                    GROUNDED_SYSTEM_PROMPT
                    + "\n\n"
                    + HTML_ARTIFACT_SYSTEM_PROMPT
                ),
            ),
            HumanMessage(
                content=user_prompt,
            ),
        ]

    def _build_grounded_messages(
        self,
        question: str,
        rag_context: RAGContext,
        history: str,
    ) -> list:
        system_prompt = GROUNDED_SYSTEM_PROMPT

        if self._is_content_writing_request(
            question
        ):
            system_prompt += (
                "\n\n"
                + CONTENT_WRITING_INSTRUCTIONS
            )

        source_mapping = (
            self._build_source_mapping(
                rag_context
            )
        )

        user_prompt = f"""
QUESTION
--------
{question}

CONVERSATION HISTORY
--------------------
{history or "No previous conversation."}

RETRIEVED TRANSCRIPT KNOWLEDGE
------------------------------
{rag_context.context_text or "No transcript knowledge was retrieved."}

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
6. Do not create a Sources or References section.
""".strip()

        return [
            SystemMessage(
                content=system_prompt,
            ),
            HumanMessage(
                content=user_prompt,
            ),
        ]

    @staticmethod
    def _build_source_mapping(
        rag_context: RAGContext,
    ) -> str:
        if not rag_context.sources:
            return "No source metadata available."

        lines: list[str] = []

        for index, source in enumerate(
            rag_context.sources,
            start=1,
        ):
            lines.append(
                f"SOURCE {index}\n"
                f"Episode: {source.episode_title}\n"
                f"Guest: {source.guest_name or 'Unknown'}\n"
                f"Timestamp: {source.timestamp or 'Unknown'}\n"
                f"URL: {source.youtube_url or 'Unknown'}"
            )

        return "\n\n".join(lines)

    @staticmethod
    def _is_ship30_request(
        question: str,
    ) -> bool:
        normalized = " ".join(
            question.lower().split()
        )

        return (
            "30 for 30" in normalized
            or "30-for-30" in normalized
            or "ship30" in normalized
        )

    @staticmethod
    def _is_html_artifact_request(
        question: str,
    ) -> bool:
        normalized = " ".join(
            question.lower().split()
        )

        html_terms = (
            "create html",
            "create an html",
            "generate html",
            "generate an html",
            "make html",
            "make an html",
            "build html",
            "build an html",
            "html page",
            "html/css",
            "html and css",
            "html + css",
            "web page",
            "webpage",
        )

        return any(
            term in normalized
            for term in html_terms
        )

    @staticmethod
    def _is_content_writing_request(
        question: str,
    ) -> bool:
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

        return any(
            phrase in normalized
            for phrase in phrases
        )

    @staticmethod
    def _message_content(message) -> str:
        content = message.content

        if isinstance(content, str):
            return content

        return str(content)