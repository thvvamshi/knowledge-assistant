# Product Requirements Document — GrowthGuide

## 1. Product Overview

GrowthGuide is a full-stack AI conversational assistant built around Lenny's Podcast transcript knowledge.

It helps product managers and growth leaders find practical, source-grounded insights without manually searching a large podcast archive.

### Core Capabilities

- Grounded conversational Q&A
- PostgreSQL + pgvector retrieval
- Local Ollama inference
- Anthropic cloud inference
- Persistent session-based conversations
- Source citations
- Ship 30 for 30 content generation
- Markdown and HTML artifact generation
- In-app artifact preview
- Sandboxed HTML rendering

The system is designed for forward deployment so another engineer can run, understand, test, and extend it with minimal onboarding.

---

## 2. Primary User

Product managers and growth leaders seeking actionable product and growth advice grounded in Lenny's Podcast content.

### User Problem

Finding relevant insights across a large transcript archive can be time-consuming.

GrowthGuide allows users to:

1. Ask product or growth questions conversationally.
2. Receive answers grounded in transcript content.
3. See supporting episodes and guests.
4. Continue conversations with preserved context.
5. Turn insights into reusable written content.
6. Generate Markdown or HTML artifacts.

### Job to Be Done

> When I have a product or growth question, I want to quickly find relevant advice from Lenny's Podcast and turn it into an actionable answer or reusable artifact, so I can make decisions and create content without manually searching the entire archive.

---

## 3. Product Goals

### Goals

- Provide source-grounded answers from Lenny's Podcast transcripts.
- Preserve independent conversation context through persistent sessions.
- Make the selected LLM provider visible.
- Support local Ollama inference.
- Support Anthropic cloud inference.
- Gracefully handle unsupported or insufficiently grounded questions.
- Generate approximately 1,250-word Ship 30 for 30-style essays.
- Generate Markdown and HTML/CSS artifacts.
- Render artifacts inside the application.
- Safely isolate generated HTML.
- Provide reproducible deployment and operational documentation.

### Non-Goals

The initial product does not include:

- General web search
- General-purpose autonomous research agents
- User authentication
- Multi-tenant administration
- General document management
- Arbitrary third-party integrations
- Hosted artifact applications

---

## 4. Success Metrics

| Metric | Target |
|---|---:|
| Retrieval citation accuracy | ≥90% |
| Local inference first-token latency | <4 seconds |
| Successful XSS vulnerabilities | 0 |
| Operational setup | Reproducible and documented |

Citation accuracy should be validated using a manually reviewed evaluation set.

Local latency depends on hardware and the selected Ollama model.

---

## 5. Assumptions

### Knowledge Scope

The available Lenny's Podcast transcript archive is the authoritative source for grounded product and growth questions.

### Grounding

If relevant transcript context cannot be retrieved, the assistant should not invent an answer from unrelated content.

Conversational messages such as greetings bypass knowledge retrieval.

### Model Availability

- Ollama is the default local provider.
- Anthropic is optional and requires an API key.

### Sessions

Sessions use UUIDs and are persisted in PostgreSQL. Authentication and multi-user ownership are outside scope.

### Artifact Security

Generated HTML is treated as untrusted content and rendered using sanitization plus a sandboxed iframe.

### Deployment

The primary handoff environment is local Docker Compose with Ollama running on the host.

---

## 6. Scope

### Included

- FastAPI backend
- Next.js frontend
- PostgreSQL
- pgvector
- Transcript ingestion
- Chunking and embeddings
- Similarity retrieval
- Grounded assistant responses
- Conversation history
- Session persistence
- Streaming responses
- Ollama provider
- Anthropic provider
- Provider fallback
- Source citations
- Ship 30 for 30 writing skill
- Markdown artifacts
- HTML artifacts
- Artifact persistence
- Artifact viewer
- HTML sanitization
- Sandboxed iframe rendering
- Health checks
- Structured logging
- Error handling
- Docker Compose
- Backend tests
- UI manual testing
- Forward-deployment documentation

### Excluded

- Authentication
- User accounts
- General internet search
- Real-time collaboration
- File-upload management
- Advanced analytics
- Enterprise role management
- Hosted production infrastructure
- Complex multi-agent orchestration

---

## 7. Core User Flows

### 7.1 Start Conversation

1. User opens GrowthGuide.
2. A new session is created.
3. The session receives a UUID.
4. The application navigates to `/chat/[sessionId]`.
5. User enters a question.

### 7.2 Grounded Question

1. User submits a question.
2. Backend loads session history.
3. Query type is resolved.
4. Knowledge questions are embedded.
5. pgvector retrieves relevant transcript chunks.
6. Grounded context is passed to the assistant.
7. The selected provider streams the response.
8. Sources and metadata are returned.
9. The assistant message is persisted.

### 7.3 Insufficient Context

If retrieval does not produce sufficiently relevant context:

1. Unrelated transcript content is not used.
2. The assistant returns a clear insufficient-information response.

### 7.4 Conversational Message

For messages such as greetings:

1. Query resolver identifies the message as conversational.
2. Transcript retrieval is skipped.
3. Assistant responds conversationally.
4. Unrelated sources are not included.

### 7.5 Provider Switching

1. User selects Ollama or Anthropic.
2. Provider is sent with the chat request.
3. Backend routes through the provider abstraction.
4. Provider/model metadata is returned.
5. Configured fallback is used if required.

### 7.6 Ship 30 for 30

1. User requests a Ship 30 for 30-style essay.
2. Relevant transcript context is retrieved.
3. Dedicated writing instructions are applied.
4. Approximately 1,250 words are generated.
5. Output includes a strong hook, skimmable structure, grounded attribution, and actionable takeaway.

### 7.7 Artifact Generation

1. User requests Markdown or HTML/CSS.
2. Assistant generates the artifact.
3. Artifact metadata is returned.
4. Artifact is persisted against the assistant message.
5. User selects **View artifact**.
6. Artifact opens in the in-app viewer.

### 7.8 Edit and Retry

#### Edit

1. User edits a previous user message.
2. Earlier conversation state is preserved.
3. Later messages are removed.
4. The edited question is processed again.
5. A replacement assistant response is generated.

#### Retry

1. User selects retry on an assistant response.
2. The preceding user question is identified.
3. The selected response and later turns are replaced.
4. The question is generated again.

---

## 8. Acceptance Criteria

### Conversations

- Users can create new conversations.
- Sessions have independent context.
- Conversations persist in PostgreSQL.
- Refresh preserves the session URL and history.
- Sidebar titles remain understandable after refresh.

### Grounding

- Relevant questions retrieve transcript context.
- Sources are returned with grounded responses.
- Unsupported questions do not receive fabricated transcript-grounded answers.
- Conversational messages do not retrieve unrelated transcript chunks.
- Follow-up questions can use conversation history.

### Providers

- Ollama can be selected.
- Anthropic can be selected when configured.
- Active provider/model is visible.
- Provider failures are handled gracefully.

### Ship 30 for 30

- Output is approximately 1,250 words.
- Opening contains a strong hook.
- Structure is skimmable.
- Guest insights are attributed to sources.
- Conclusion provides an actionable takeaway.

### Artifacts

- Markdown artifacts render correctly.
- HTML/CSS artifacts render correctly.
- Artifacts are associated with their generating assistant message.
- HTML is sanitized before rendering.
- HTML is rendered in a sandboxed iframe.
- Artifact rendering remains inside the application.

### Operations

- Docker Compose starts the core services.
- Configuration is documented.
- Secrets are not committed.
- Health status is available.
- Failures produce understandable errors.
- Automated tests cover critical backend behavior.

---

## 9. Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| LLM hallucination | High | Retrieval threshold, grounded prompts, citations, refusal behavior |
| Poor local model reasoning | Medium | Ollama evaluation and optional Anthropic fallback |
| Local inference latency | Medium | Small local model and streaming |
| Retrieval mismatch | High | Similarity threshold, top-k retrieval, evaluation |
| Insufficient transcript context | High | Explicit refusal |
| Database failure | High | Health checks, rollback, structured errors |
| Provider outage | Medium | Provider abstraction and fallback |
| Unsafe generated HTML | High | DOMPurify + sandboxed iframe |
| Large artifacts | Medium | Dedicated artifact rendering and persistence |
| Session corruption | Medium | Explicit relationships and transactional edits/retries |
| Configuration errors | Medium | `.env.example` and documented defaults |
| Model quality differences | Medium | Provider/model metadata in UI |

---

## 10. Key Trade-offs

### Local-First vs Cloud Quality

Ollama provides a low-cost local workflow but depends on local hardware and model quality.

Anthropic provides cloud-model capability but introduces API dependency and cost.

A provider abstraction keeps the application independent of either provider.

### Strict Grounding vs Answer Coverage

The assistant may refuse questions that a general LLM could answer.

This is intentional: source trustworthiness is prioritized over answer coverage.

### Simplicity vs Feature Breadth

The implementation focuses on grounded retrieval, conversation, artifact generation, and operational handoff rather than unrelated features.

### Sandboxing vs Full HTML Capability

Sandboxing limits generated HTML capabilities but provides a safer boundary between model-generated content and the application.

---

## 11. Implementation Plan

### Phase 1 — Foundation

- FastAPI application
- PostgreSQL + pgvector
- Configuration
- Session/message persistence

### Phase 2 — Knowledge Layer

- Transcript loading
- Parsing
- Chunking
- Embeddings
- Vector retrieval
- Source metadata

### Phase 3 — Agent and Providers

- Provider abstraction
- Ollama
- Anthropic
- Fallback behavior
- Grounded assistant
- Conversational routing

### Phase 4 — Content and Artifacts

- Ship 30 for 30 skill
- Markdown artifacts
- HTML artifacts
- Artifact persistence
- Sanitization and sandboxing

### Phase 5 — Frontend

- Session sidebar
- Chat interface
- Streaming responses
- Provider selector
- Source cards
- Artifact viewer
- Responsive behavior

### Phase 6 — Operational Readiness

- Health checks
- Logging
- Error handling
- Docker Compose
- Tests
- Documentation
- Final validation

---

## 12. Definition of Done

GrowthGuide is ready for handoff when:

- Core chat works end-to-end.
- Grounded answers provide useful source attribution.
- Unsupported questions are handled safely.
- Ollama works locally.
- Anthropic works when configured.
- Sessions persist across refreshes.
- Markdown and HTML artifacts render in-app.
- Generated HTML is sanitized and isolated.
- Automated tests pass.
- Docker Compose startup is documented and validated.
- README, PRD, architecture, and design documentation are complete.
- Final demo covers the product and key technical trade-offs.
