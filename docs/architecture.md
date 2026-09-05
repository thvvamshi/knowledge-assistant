# Architecture

This document describes the system structure, runtime flows, deployment model, and key architectural decisions for Lenny Growth Assistant.

## 1. Overview

Lenny Growth Assistant is a full-stack AI conversational application that combines:

- Next.js frontend
- FastAPI backend
- PostgreSQL with pgvector
- Lenny Podcast transcript knowledge base
- Ollama for local inference
- Anthropic as an optional cloud provider
- Streaming responses
- Persistent conversation sessions
- Markdown and HTML artifact generation

The architecture is designed around three core requirements:

1. **Ground answers in Lenny Podcast content.**
2. **Keep conversations persistent and independently addressable.**
3. **Support local-first development while allowing cloud LLM providers.**

---

## 2. High-Level Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                         Next.js                             │
│                         Frontend                            │
│                                                             │
│  Sidebar ─── Chat ─── Message History ─── Artifact Viewer  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                    HTTP / NDJSON
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                         FastAPI                             │
│                         Backend                             │
│                                                             │
│  Sessions │ Messages │ Chat │ Providers │ Health           │
│                                                             │
│  Query Resolution → Retrieval → Agent → Response           │
└───────────────┬──────────────────────────┬──────────────────┘
                │                          │
                ▼                          ▼
┌──────────────────────────┐    ┌────────────────────────────┐
│ PostgreSQL + pgvector    │    │       LLM Providers        │
│                          │    │                            │
│ Sessions                 │    │ Ollama                     │
│ Messages                 │    │ Anthropic                  │
│ Artifacts                │    │                            │
│ Transcript chunks        │    └────────────────────────────┘
│ Embeddings               │
└──────────────▲───────────┘
               │
               │
┌──────────────┴───────────┐
│   Lenny Podcast Data     │
│                          │
│ Transcript ingestion     │
│ Chunking                 │
│ Embeddings               │
└──────────────────────────┘
````

---

## 3. Technology Stack

### Frontend

* Next.js 16
* React 19
* TypeScript
* Tailwind CSS
* react-markdown
* remark-gfm
* DOMPurify
* Sandboxed iframe for HTML artifacts

### Backend

* FastAPI
* Python
* SQLAlchemy async
* Pydantic
* PostgreSQL
* pgvector
* Local embedding model
* Ollama
* Anthropic

### Infrastructure

* Docker
* Docker Compose
* PostgreSQL container
* FastAPI container
* Host Ollama for local inference

---

## 4. Repository Structure

```text
lenny-growth-assistant/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── services/
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── hooks/
│   │   └── lib/
│   ├── Dockerfile
│   └── package.json
│
├── data/
│   └── lenny-transcripts-source/
│
├── docs/
│   ├── PRD.md
│   ├── architecture.md
│   └── design.md
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 5. Frontend Architecture

The frontend uses the Next.js App Router.

```text
frontend/src/
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   ├── globals.css
│   └── chat/
│       └── [sessionId]/
│           └── page.tsx
│
├── components/
│   ├── chat/
│   │   ├── ChatPane.tsx
│   │   ├── MessageInput.tsx
│   │   └── MessageItem.tsx
│   │
│   ├── sidebar/
│   │   └── Sidebar.tsx
│   │
│   └── artifact/
│       ├── ArtifactViewer.tsx
│       ├── MarkdownArtifact.tsx
│       └── SandboxedIframe.tsx
│
├── hooks/
│   └── useChatStream.ts
│
└── lib/
    ├── api.ts
    └── artifact.ts
```

### Responsibilities

**App**

Handles application and session routes.

**Chat components**

Render conversations, messages, input controls, provider selection, edit/retry actions, and streaming states.

**Sidebar**

Displays available sessions and allows navigation between conversations.

**Artifact components**

Render generated Markdown and HTML artifacts independently from normal chat messages.

**useChatStream**

Handles the streaming `/api/chat` connection and converts NDJSON events into frontend state updates.

**api.ts**

Contains API communication and shared frontend types.

---

## 6. Backend Architecture

The backend is organized around API routes, services, agents, persistence, and retrieval.

```text
backend/app/
├── agents/
├── api/
├── core/
├── db/
├── models/
├── schemas/
└── services/
```

### API Layer

Responsible for:

* Request validation
* HTTP responses
* Session management
* Message management
* Streaming chat
* Provider discovery
* Health checks

### Services Layer

Responsible for application logic such as:

* Retrieval
* RAG context construction
* Assistant orchestration
* Artifact generation
* Provider handling

### Agents

Responsible for constructing the appropriate LLM prompts and invoking the configured model provider.

### Database Layer

Responsible for:

* SQLAlchemy models
* Async database sessions
* PostgreSQL persistence
* pgvector operations

---

## 7. Database Architecture

PostgreSQL is used as the primary persistent store.

pgvector is used for transcript embeddings and similarity search.

Conceptually, the data model is:

```text
Session
   │
   ├── Message
   │     └── Artifact
   │
   └── Message

Transcript
   │
   └── Transcript Chunk
             │
             └── Embedding
```

### Sessions

Store conversation identity and metadata.

Important fields include:

* ID
* Title
* Created timestamp
* Updated timestamp

### Messages

Store conversation history.

Important fields include:

* ID
* Session ID
* Role
* Content
* Provider
* Model
* Created timestamp

### Artifacts

Store generated artifacts associated with assistant messages.

Important fields include:

* Artifact type
* Title
* Content
* Message association

### Transcript Chunks

Store searchable sections of Lenny Podcast transcripts together with metadata and embeddings.

---

## 8. Knowledge Ingestion

The knowledge base is built from Lenny Podcast transcripts.

The ingestion pipeline is:

```text
Transcript Files
      │
      ▼
Parsing
      │
      ▼
Chunking
      │
      ▼
Embedding Generation
      │
      ▼
PostgreSQL + pgvector
```

Transcript metadata is retained so retrieved chunks can be connected to:

* Episode title
* Guest name
* Timestamp
* Source URL

This metadata is later returned as source citations.

---

## 9. Retrieval Architecture

Knowledge questions use retrieval before generation.

```text
User Question
      │
      ▼
Query Resolver
      │
      ├── Conversational?
      │       │
      │       └── Skip retrieval
      │
      ▼
Retrieval Query
      │
      ▼
Vector / Hybrid Retrieval
      │
      ▼
Relevant Transcript Chunks
      │
      ▼
RAG Context
      │
      ▼
Assistant Agent
```

The retrieval layer uses similarity thresholds and a configurable top-k result count.

The system intentionally distinguishes between:

* Conversational messages
* Knowledge questions
* Questions where no relevant context can be retrieved

This prevents unrelated transcript content from being injected into simple conversational interactions.

---

## 10. Conversational Query Handling

Clearly conversational messages bypass the knowledge retrieval pipeline.

For example:

```text
Hi
Hello
Thanks
How are you?
```

are handled directly by the conversational agent.

This is important because retrieving transcript chunks for these messages can produce irrelevant context and lead to incorrect answers.

For knowledge questions, retrieval remains mandatory.

---

## 11. Grounded Answer Flow

For a knowledge question:

```text
Question
   │
   ▼
Query Resolver
   │
   ▼
Retrieve Transcript Chunks
   │
   ▼
Build Grounded Context
   │
   ▼
Assistant Agent
   │
   ▼
Grounded Answer
   │
   ├── Source metadata
   │
   └── Optional Artifact
```

If the question is outside the available knowledge base and no useful context is retrieved, the system returns a grounded refusal instead of inventing an answer.

---

## 12. Agent Architecture

The assistant agent selects a system prompt based on the request type.

Conceptually:

```text
                    User Request
                         │
                         ▼
                 Request Classification
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
   Conversational     Ship30       HTML Artifact
          │              │              │
          ▼              ▼              ▼
 Conversational      Writing        HTML System
    Prompt            Prompt           Prompt
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                   LLM Provider
```

Grounded knowledge questions use the grounded system prompt with retrieved context.

---

## 13. Provider Architecture

The application supports multiple LLM providers behind a common interface.

```text
                 Assistant Service
                        │
                        ▼
                 Provider Selection
                        │
              ┌─────────┴─────────┐
              ▼                   ▼
           Ollama              Anthropic
              │                   │
              ▼                   ▼
        Local Model          Cloud Model
```

### Ollama

Used as the default local provider.

Current development configuration:

```text
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:4b
```

### Anthropic

Optional cloud provider:

```text
ANTHROPIC_API_KEY
ANTHROPIC_MODEL
```

The backend can fall back to another configured provider when the selected provider is unavailable.

---

## 14. Provider Discovery

The frontend obtains provider information from:

```text
GET /api/providers
```

The response contains:

* Provider ID
* Display name
* Model
* Configured status
* Availability status

The frontend uses this information to show only usable provider choices.

---

## 15. Streaming Architecture

Chat responses are streamed using NDJSON.

```text
Frontend
   │
   │ POST /api/chat
   ▼
FastAPI
   │
   ▼
Assistant Service
   │
   ▼
LLM Provider
   │
   │ streamed tokens
   ▼
FastAPI
   │
   │ NDJSON events
   ▼
Frontend
```

Supported event types include:

```text
sources
metadata
token
artifact
complete
artifact_saved
error
```

This allows the frontend to:

* Display tokens incrementally
* Show provider/model information
* Display source citations
* Detect generated artifacts
* Handle errors without losing the entire conversation

---

## 16. Chat Persistence

Normal conversation flow:

```text
User Message
     │
     ▼
Persist User Message
     │
     ▼
Generate Assistant Response
     │
     ▼
Persist Assistant Message
     │
     ▼
Persist Artifact if Generated
```

This ensures conversations survive browser refreshes and can be reopened through their session URL.

---

## 17. Edit and Retry

The backend provides dedicated message operations.

### Edit

```text
PATCH /api/sessions/{session_id}/messages/{message_id}
```

The system:

1. Validates the target user message.
2. Preserves the required conversation history.
3. Updates the user message.
4. Removes later messages/artifacts.
5. Regenerates the assistant response.

### Retry

```text
POST /api/sessions/{session_id}/messages/{message_id}/retry
```

The system:

1. Finds the target assistant response.
2. Uses the conversation history before that response.
3. Removes the target and later messages/artifacts.
4. Regenerates the assistant response.

This keeps conversation branching deterministic rather than simply appending another response.

---

## 18. Artifact Architecture

Artifacts are generated separately from normal response rendering.

Supported types:

```text
Markdown
HTML
```

The flow is:

```text
User Request
     │
     ▼
Artifact Detection
     │
     ▼
LLM Generation
     │
     ▼
Artifact Cleaning
     │
     ▼
Persist Artifact
     │
     ▼
Attach to Assistant Message
     │
     ▼
User clicks "View artifact"
     │
     ▼
Artifact Viewer
```

Artifacts are not automatically opened when generated.

---

## 19. Markdown Artifacts

Markdown artifacts are rendered using:

```text
react-markdown
remark-gfm
```

This supports:

* Headings
* Paragraphs
* Lists
* Tables
* Blockquotes
* Links
* Code blocks
* GitHub-flavored Markdown

---

## 20. HTML Artifact Security

Generated HTML is treated as untrusted content.

The application uses two layers of protection:

### Sanitization

DOMPurify removes dangerous HTML elements and attributes before rendering.

### Sandboxed iframe

Sanitized HTML is rendered using an iframe with:

```html
sandbox="allow-scripts"
```

`allow-same-origin` is intentionally omitted.

The goal is to prevent generated HTML from gaining normal access to the parent application context.

---

## 21. API Architecture

The primary backend routes are:

```text
GET    /api/health

GET    /api/providers

POST   /api/sessions
GET    /api/sessions
GET    /api/sessions/{session_id}

GET    /api/sessions/{session_id}/messages
POST   /api/sessions/{session_id}/messages
PATCH  /api/sessions/{session_id}/messages/{message_id}
POST   /api/sessions/{session_id}/messages/{message_id}/retry

POST   /api/chat
```

The streaming chat endpoint is responsible for the primary AI interaction.

---

## 22. Error Handling

The API uses structured errors where appropriate.

Examples include:

```text
SESSION_NOT_FOUND
DATABASE_UNAVAILABLE
ASSISTANT_UNAVAILABLE
```

Streaming errors are represented as NDJSON events so the frontend can display a useful failure state.

Request IDs are included for troubleshooting and correlation.

---

## 23. Health and Resilience

The backend health endpoint checks core dependencies.

Conceptually:

```text
/api/health
     │
     ├── Database
     ├── Ollama
     └── Vector Index
```

The application is designed to distinguish between:

* Application errors
* Database failures
* Provider failures
* Retrieval failures
* Invalid sessions

This prevents infrastructure failures from being presented as normal assistant responses.

---

## 24. Configuration

Configuration is environment-driven.

Important variables include:

```env
DATABASE_URL
LLM_PROVIDER

OLLAMA_BASE_URL
OLLAMA_MODEL

ANTHROPIC_API_KEY
ANTHROPIC_MODEL

EMBEDDING_MODEL

TRANSCRIPT_SOURCE_DIR

CORS_ORIGINS
```

Secrets such as API keys are not committed to the repository.

`.env.example` documents the expected configuration.

---

## 25. Local Deployment

The development topology is:

```text
┌──────────────────────┐
│ Browser              │
│ localhost:3000       │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Next.js              │
│ Frontend              │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ FastAPI Container    │
│ localhost:8000       │
└───────┬──────────────┘
        │
        ├──────────────► PostgreSQL + pgvector
        │
        └──────────────► Ollama on host
```

Docker Compose currently manages the backend and database services.

The Next.js frontend runs separately with:

```bash
npm run dev
```

---

## 26. Key Architectural Decisions

## PostgreSQL + pgvector

Chosen to keep relational application data and vector retrieval in one database.

Benefits:

* Simple local setup
* Persistent sessions
* Persistent messages
* Vector similarity search
* Fewer infrastructure dependencies

## Ollama First

Ollama provides a local/free development path and satisfies the local inference requirement.

Anthropic remains available as an optional cloud provider.

## Streaming NDJSON

NDJSON provides a simple streaming protocol that supports:

* Token streaming
* Metadata
* Sources
* Artifacts
* Completion
* Errors

without requiring a more complex realtime infrastructure.

## Explicit Artifact Viewer

Artifacts are attached to the relevant assistant message and opened intentionally by the user.

This keeps the normal chat experience focused while still providing a dedicated workspace for generated content.

## Sandboxed HTML

Generated HTML is untrusted model output, so it is sanitized and rendered in an isolated iframe rather than directly inserted into the application DOM.

---

## 27. Main Request Flow

A complete knowledge request follows this path:

```text
User
 │
 ▼
Next.js Chat UI
 │
 ▼
POST /api/chat
 │
 ▼
FastAPI
 │
 ▼
Load Session History
 │
 ▼
Query Resolver
 │
 ▼
Retrieve Relevant Transcript Chunks
 │
 ▼
Build Grounded Context
 │
 ▼
Assistant Agent
 │
 ▼
Selected LLM Provider
 │
 ▼
Stream Response
 │
 ├──────────────► Tokens
 │
 ├──────────────► Sources
 │
 ├──────────────► Metadata
 │
 └──────────────► Artifact
 │
 ▼
Persist Assistant Message
 │
 ▼
Persist Artifact
 │
 ▼
Frontend Updates UI
```

---

## 28. Design Principles

The architecture follows these principles:

1. **Ground before generating** for knowledge questions.
2. **Do not retrieve unnecessarily** for simple conversational messages.
3. **Persist conversation state** so sessions survive refreshes.
4. **Keep provider selection flexible** through a common provider layer.
5. **Stream responses** for responsive interaction.
6. **Treat generated HTML as untrusted.**
7. **Keep artifacts attached to the response that generated them.**
8. **Prefer local-first development** while supporting cloud inference.
9. **Keep infrastructure simple** for a take-home assignment.
10. **Favor clear boundaries** between API, services, retrieval, agents, and persistence.

---

## 29. Current Scope

The architecture currently supports:

* Persistent sessions
* Persistent messages
* Transcript-based RAG
* Source citations
* Conversational query bypass
* Ollama
* Anthropic
* Provider fallback
* Streaming responses
* Edit
* Retry
* Markdown artifacts
* HTML artifacts
* Sandboxed artifact rendering
* Responsive frontend
* Health checks
* Structured errors
* Request IDs

The architecture intentionally avoids unnecessary infrastructure and keeps the implementation suitable for local development, evaluation, and demonstration.