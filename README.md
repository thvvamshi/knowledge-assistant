# Lenny Growth Assistant

A full-stack AI conversational assistant grounded in Lenny Podcast transcripts. It supports persistent conversations, streaming responses, source citations, provider and model selection, and generated Markdown and HTML artifacts.

## Features

- Conversational AI with session-based chat history
- Grounded answers based on Lenny Podcast transcripts
- Source citations with episode, guest, timestamp, and URL
- Local Ollama support for free inference
- Optional Anthropic support with provider fallback
- Streaming NDJSON responses
- Persistent conversations in PostgreSQL + pgvector
- Edit and retry conversation messages
- Markdown and HTML artifact generation
- Sandboxed HTML artifact rendering
- Responsive ChatGPT-style interface
- Health checks, structured errors, and request IDs

## Architecture

```text
                    ┌─────────────────────┐
                    │      Next.js        │
                    │      Frontend       │
                    └──────────┬──────────┘
                               │
                               │ HTTP / NDJSON
                               ▼
                    ┌─────────────────────┐
                    │       FastAPI       │
                    │       Backend       │
                    └──────┬──────┬───────┘
                           │      │
                ┌──────────┘      └──────────┐
                ▼                            ▼
       ┌────────────────┐           ┌────────────────┐
       │ PostgreSQL +   │           │ LLM Providers  │
       │ pgvector       │           │ Ollama /       │
       │                │           │ Anthropic      │
       └────────────────┘           └────────────────┘
                ▲
                │
       ┌────────────────┐
       │ Lenny Podcast  │
       │ Transcripts    │
       └────────────────┘
````

## Repository Structure

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
│   │   ├── services/
│   │   └── main.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── hooks/
│   │   └── lib/
│   ├── package.json
│   └── Dockerfile
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

## Prerequisites

Install the following:

* Docker Desktop
* Node.js 20+
* npm
* Ollama

For local inference, install the configured Ollama model:

```bash
ollama pull gemma3:4b
```

Start Ollama:

```bash
ollama serve
```

## Environment Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Important variables:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/lenny

LLM_PROVIDER=ollama

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:4b

ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-3-5-sonnet-latest

EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

CORS_ORIGINS=http://localhost:3000
```

Anthropic is optional; the application is designed to work locally with Ollama.

## Start the Backend

From the project root, start the backend and database:

```bash
docker compose up --build
```

Docker Compose starts the backend and database services.

Services:

```text
FastAPI:    http://localhost:8000
PostgreSQL: localhost:5432
```

Health check:

```text
http://localhost:8000/api/health
```

## Start the Frontend

The frontend runs separately from Docker Compose:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

## Knowledge Base

The application uses Lenny Podcast transcripts as its knowledge base.

Transcript files are mounted into the backend container from:

```text
data/lenny-transcripts-source/episodes
```

The retrieval pipeline uses:

```text
User Question
     │
     ▼
Query Resolver
     │
     ▼
Embedding / Vector Retrieval
     │
     ▼
Relevant Transcript Chunks
     │
     ▼
Grounded Agent Context
     │
     ▼
Answer + Source Citations
```

Conversational messages, such as greetings, bypass retrieval so unrelated transcript content is not added to the response.

## Grounded Answers

Knowledge questions are answered using retrieved transcript context.

Example:

```text
What did Sean Ellis say about growth teams?
```

The response can include:

* Answer
* Episode
* Guest
* Timestamp
* Source URL

If relevant knowledge cannot be retrieved, the assistant does not invent an answer.

Conversational messages such as:

```text
Hi
```

are handled directly without unnecessary knowledge-base retrieval.

## Providers

The application supports:

### Ollama

Local and free inference.

```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=gemma3:4b
```

### Anthropic

Optional cloud provider.

```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_key
ANTHROPIC_MODEL=claude-3-5-sonnet-latest
```

The backend falls back to another provider when the selected provider is unavailable.

The frontend exposes the available provider/model selection inside the chat input.

## Streaming

Chat responses are streamed from FastAPI using NDJSON.

The frontend handles events such as:

```text
sources
metadata
token
artifact
complete
artifact_saved
error
```

This allows the UI to display responses progressively instead of waiting for completion.

## Conversations

Each conversation has its own session ID and persistent message history.

Routes include:

```text
POST /api/sessions
GET  /api/sessions
GET  /api/sessions/{session_id}
GET  /api/sessions/{session_id}/messages
POST /api/sessions/{session_id}/messages
PATCH /api/sessions/{session_id}/messages/{message_id}
POST /api/sessions/{session_id}/messages/{message_id}/retry
```

Conversation URLs use the session ID:

```text
/chat/{sessionId}
```

This makes conversations independently addressable and reloadable.

## Edit and Retry

Users can edit messages and regenerate responses.

Assistant messages can be retried using the selected provider.

When a message is edited or retried, later conversation state is removed so the regenerated response uses the corrected history.

## Artifacts

The assistant can generate artifacts when a request calls for a document, Markdown output, HTML page, or similar deliverable.

Supported types:

```text
Markdown
HTML
```

Example requests:

```text
Create a 30-for-30 essay about product growth.
```

```text
Create an HTML landing page for a growth product.
```

Artifacts are attached to the relevant assistant message and are opened explicitly through:

```text
View artifact
```

The artifact panel does not open automatically for every response.

## Artifact Security

HTML artifacts are treated as untrusted content.

Before rendering:

* Dangerous elements are removed.
* Event-handler attributes are removed.
* External resource elements are restricted.
* HTML is rendered inside a sandboxed iframe.

The iframe uses:

```html
sandbox="allow-scripts"
```

`allow-same-origin` is intentionally not enabled.

This isolates generated HTML from the main application as much as practical.

## Ship 30 for 30

The assistant supports Ship 30 for 30 style essay generation.

The writing workflow emphasizes:

* Strong opening hook
* One central thesis
* Clear problem/context
* Practical insight
* Supporting evidence from relevant sources
* Skimmable structure
* Practical conclusion
* Approximately 1,250 words

The generated essay is grounded in relevant Lenny Podcast material rather than simply summarizing several guests.

## API Overview

### Health

```text
GET /api/health
```

### Providers

```text
GET /api/providers
```

### Sessions

```text
POST /api/sessions
GET  /api/sessions
GET  /api/sessions/{session_id}
```

### Messages

```text
GET   /api/sessions/{session_id}/messages
POST  /api/sessions/{session_id}/messages
PATCH /api/sessions/{session_id}/messages/{message_id}
POST  /api/sessions/{session_id}/messages/{message_id}/retry
```

### Streaming Chat

```text
POST /api/chat
```

Request:

```json
{
  "session_id": "session-uuid",
  "content": "What did Sean Ellis say about growth teams?",
  "provider": "ollama",
  "generate_artifact": false
}
```

## Testing

Backend tests:

```bash
cd backend
pytest
```

Frontend lint:

```bash
cd frontend
npm run lint
```

Frontend production build:

```bash
cd frontend
npm run build
```

## Manual UI Verification

Verify the following workflows:

1. Open the application.
2. Create a new conversation.
3. Send a conversational message such as `Hi`.
4. Send a knowledge question about Lenny Podcast content.
5. Confirm relevant source citations are displayed.
6. Send an out-of-domain question and confirm the assistant refuses without inventing an answer.
7. Switch between available providers.
8. Refresh the page and confirm the conversation persists.
9. Open another session and confirm its history is independent.
10. Edit a user message and regenerate the response.
11. Retry an assistant response.
12. Generate a Markdown artifact.
13. Open the artifact from its message.
14. Generate an HTML artifact.
15. Confirm HTML renders inside the isolated artifact viewer.
16. Close the artifact viewer.
17. Test the layout on a smaller viewport.

## Troubleshooting

### Ollama is unavailable

Check:

```bash
ollama list
```

Confirm the configured model exists:

```bash
ollama pull gemma3:4b
```

Confirm Ollama is running:

```bash
ollama serve
```

### Backend is unavailable

Check containers:

```bash
docker compose ps
```

View backend logs:

```bash
docker compose logs backend
```

View database logs:

```bash
docker compose logs db
```

### Frontend cannot reach backend

Confirm:

```text
Frontend: http://localhost:3000
Backend:  http://localhost:8000
```

Check:

```env
CORS_ORIGINS=http://localhost:3000
```

### Database is unavailable

Check:

```bash
docker compose ps
```

The PostgreSQL container should report a healthy status before the backend starts.

## Security Considerations

The application treats generated HTML as untrusted content.

Security measures include:

* HTML sanitization
* Sandboxed iframe rendering
* No `allow-same-origin`
* No direct execution of generated HTML in the main application DOM
* Provider/API credentials kept in environment variables
* Structured API errors
* Request IDs for troubleshooting

Generated content should still be treated as untrusted user or model output.

## Local-First Design

The default development setup uses:

```text
Ollama
PostgreSQL
pgvector
FastAPI
Next.js
```

This keeps the core development workflow local and avoids requiring a paid provider.

Anthropic can be enabled when cloud inference is preferred.

## Documentation

Additional project documentation:

```text
docs/PRD.md
docs/architecture.md
docs/design.md
```

These documents describe the product requirements, technical architecture, and frontend interaction and design decisions.

## Project Status

The application currently includes:

* Persistent conversations
* Session isolation
* Grounded RAG answers
* Source citations
* Ollama support
* Anthropic support
* Provider fallback
* Streaming responses
* Edit/retry
* Markdown artifacts
* HTML artifacts
* Sandboxed artifact rendering
* Responsive chat UI
* Product and technical documentation

```