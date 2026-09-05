# Design

## 1. Design Overview

Lenny Growth Assistant uses a focused, conversational interface organized around three primary areas:

```text
┌──────────────┬──────────────────────────────┬─────────────────────┐
│   Sidebar    │          Chat                │  Artifact Viewer    │
│              │                              │                     │
│ Conversations│      Message History         │  Generated Content  │
│              │                              │                     │
│ New Chat     │      Assistant Response      │  Markdown / HTML    │
│              │                              │                     │
│ Session List │      Message Input           │                     │
└──────────────┴──────────────────────────────┴─────────────────────┘
````

The artifact viewer remains closed during normal conversation and opens only when the user selects an artifact attached to an assistant message.

---

# 2. Design Goals

The interface prioritizes:

* Simple conversational interaction
* Clear conversation history
* Fast access to previous sessions
* Visible streaming responses
* Clear provider and model selection
* Clear source citations
* Explicit artifact interaction
* Secure HTML rendering
* Responsive behavior
* Accessible controls
* Minimal visual complexity

The interface should feel familiar without unnecessarily copying another product's visual identity.

---

# 3. Information Architecture

The application has three primary areas.

### Sidebar

Used to:

* Creating a new conversation
* Viewing previous conversations
* Switching between sessions
* Collapsing the navigation area

### Chat

Used to:

* Reading conversation history
* Sending messages
* Viewing streaming responses
* Viewing sources
* Editing user messages
* Retrying assistant responses
* Opening generated artifacts

### Artifact Viewer

Used to:

* Viewing generated Markdown
* Viewing generated HTML
* Closing the artifact workspace

The artifact viewer is contextual to the selected assistant message.

---

# 4. Application Layout

## Desktop

```text
┌─────────────────────────────────────────────────────────────┐
│ Sidebar        │ Chat Area                    │ Artifact     │
│                │                              │ Viewer       │
│ New Chat       │                              │              │
│                │ Message                     │              │
│ Conversation 1 │                              │ Artifact      │
│ Conversation 2 │ Assistant                   │ Content      │
│ Conversation 3 │                              │              │
│                │                              │              │
│                │ Input + Provider             │              │
└─────────────────────────────────────────────────────────────┘
```

When no artifact is selected:

```text
┌──────────────┬──────────────────────────────────────────────┐
│ Sidebar      │ Chat                                         │
│              │                                              │
│ Sessions     │ Messages                                     │
│              │                                              │
│              │                                              │
│              │ Input                                        │
└──────────────┴──────────────────────────────────────────────┘
```

---

# 5. Sidebar

The sidebar provides conversation navigation and session management.

## Contents

* New conversation action
* Session history
* Active session indicator
* Collapse control

When the backend does not provide a custom title, the conversation title is derived from the conversation content.

Example:

```text
New Chat

What did Sean Ellis say...
Create a growth strategy...
Product-led growth...
```

The sidebar should remain visually secondary to the active conversation.

---

# 6. Sidebar States

### Expanded

The full session list is visible.

```text
┌──────────────────────┐
│ ☰  GrowthGuide       │
│                      │
│ + New chat            │
│                      │
│ Recent               │
│                      │
│ Growth teams...       │
│ Product strategy...   │
│ Ship 30 essay...      │
└──────────────────────┘
```

### Collapsed

Only essential navigation controls remain visible.

```text
┌──────┐
│  ☰   │
│  +   │
│  •   │
│  •   │
└──────┘
```

### Mobile

The sidebar behaves as a drawer and can be opened or closed without permanently reducing the chat viewport.

---

# 7. Chat Area

The chat is the primary workspace and the main focus of the interface.

The layout should provide:

* A comfortable reading width
* Clear separation between user and assistant messages
* Visible streaming state
* A persistent input area
* Minimal header chrome

The active conversation should remain the dominant visual element.

---

# 8. User Messages

User messages should be visually distinct while remaining simple.

Each user message supports:

* Message content
* Edit action
* Save and retry after editing
* Copy action

Editing should replace the message with an editable field rather than opening a separate page or modal.

Example:

```text
You
────────────────────────────
What did Sean Ellis say about
growth teams?

Edit   Copy
```

During editing:

```text
┌─────────────────────────────────┐
│ What did Sean Ellis say about   │
│ growth teams?                   │
└─────────────────────────────────┘

Cancel     Save & retry
```

---

# 9. Assistant Messages

Assistant responses should display:

* Assistant identity
* Provider/model metadata
* Response content
* Source citations when available
* Artifact attachment when available
* Copy action
* Retry action

Example:

```text
GrowthGuide
Ollama · gemma3:4b

Sean Ellis describes growth teams as...

Sources
────────────────────────────
Lenny Podcast · Sean Ellis
Timestamp · 32:14
Open source

[ Generated artifact ]
View artifact

Copy    Retry
```

---

# 10. Streaming State

Streaming responses should appear progressively as they are generated.

The interface should not make the user wait for the entire response before showing content.

Conceptually:

```text
GrowthGuide
Ollama · gemma3:4b

Growth teams typically...
```

While streaming, the UI may show a subtle activity indicator.

The input should prevent accidental duplicate submissions while a request is actively streaming.

---

# 11. Provider Selector

Provider and model selection belongs inside the message input area rather than in the primary application header.

Example:

```text
┌─────────────────────────────────────────────┐
│ Ask GrowthGuide anything...                 │
│                                             │
│ Ollama · gemma3:4b                    ↑     │
└─────────────────────────────────────────────┘
```

The selector should show only providers that are configured and available.

Provider information should be understandable without requiring the user to understand backend implementation details.

---

# 12. Message Input

The message input is the primary action control.

Requirements:

* Multi-line text input
* Send button
* Provider/model selector
* A disabled state while empty
* Streaming/loading state
* Keyboard-friendly interaction

The input should remain visually anchored near the bottom of the chat workspace.

Example:

```text
┌─────────────────────────────────────────────┐
│ Ask a question about Lenny's content...     │
│                                             │
│ Ollama · gemma3:4b                    [➤]   │
└─────────────────────────────────────────────┘
```

---

# 13. Source Citations

Sources should be presented separately from the assistant's main response.

This avoids making citations difficult to distinguish from the generated answer.

Example:

```text
Sources

┌──────────────────────────────────────┐
│ Lenny Podcast                        │
│ Sean Ellis                           │
│ 32:14                                │
│ Open source ↗                        │
└──────────────────────────────────────┘
```

A source card should expose useful metadata without overwhelming the response.

For conversational messages that do not use retrieval, no source section should be displayed.

---

# 14. Artifact Interaction

Artifacts are attached to the assistant message that generated them.

They should not automatically open the artifact viewer.

Example:

```text
┌──────────────────────────────────────┐
│ Generated artifact                   │
│ Ship 30 for 30 Essay                 │
│ Markdown                             │
│                                      │
│ View artifact →                      │
└──────────────────────────────────────┘
```

The user explicitly chooses when to open the artifact.

This keeps normal conversations focused on the answer.

---

# 15. Artifact Viewer

The artifact viewer is a dedicated right-side workspace on desktop and a drawer or full-screen overlay on smaller screens.

```text
┌──────────────────────────────────────┐
│ Artifact                         ×   │
│ Markdown                             │
├──────────────────────────────────────┤
│                                      │
│ # Generated Essay                    │
│                                      │
│ Content rendered natively            │
│                                      │
│ ## Growth Teams                      │
│                                      │
│ ...                                  │
│                                      │
└──────────────────────────────────────┘
```

The viewer includes:

* Artifact title
* Artifact type
* Close action
* Scrollable content area

---

# 16. Markdown Artifact Rendering

Markdown is rendered as formatted content rather than raw Markdown syntax.

Supported presentation includes:

* Headings
* Paragraphs
* Ordered lists
* Unordered lists
* Tables
* Blockquotes
* Links
* Inline code
* Code blocks

The typography should prioritize readability for long-form content.

---

# 17. HTML Artifact Rendering

HTML artifacts are rendered inside a sandboxed iframe.

The design intentionally isolates generated HTML from the application's main DOM.

The rendering flow is:

```text
Generated HTML
      │
      ▼
Sanitize
      │
      ▼
Sandboxed iframe
      │
      ▼
Artifact Viewer
```

The iframe uses a restricted sandbox configuration.

```html
sandbox="allow-scripts"
```

`allow-same-origin` is not enabled.

---

# 18. Artifact States

### No Artifact

The artifact viewer is not displayed.

### Artifact Available

The assistant message displays a `View artifact` action.

### Artifact Open

The viewer appears on the right side on desktop.

### Artifact Closed

The viewer disappears and the chat returns to the full available width.

### Mobile

The artifact viewer behaves as a drawer or full-width overlay so the chat remains usable.

---

# 19. Responsive Design

The interface adapts across viewport sizes without requiring horizontal scrolling.

## Desktop

```text
Sidebar + Chat + Artifact Viewer
```

## Tablet

```text
Sidebar + Chat
Artifact Viewer as contextual panel
```

## Mobile

```text
Chat
  │
  ├── Sidebar drawer
  │
  └── Artifact drawer
```

The primary conversation remains usable without horizontal scrolling.

---

# 20. Navigation

Session URLs use the session identifier:

```text
/chat/{sessionId}
```

This allows a conversation to be:

* Refreshed
* Reopened
* Navigated directly
* Kept independent from other sessions

Switching sessions updates the chat history without mixing messages between conversations.

---

# 21. Loading States

Loading states should clearly communicate progress without blocking the entire application.

Examples:

### Loading sessions

```text
Loading conversations...
```

### Loading messages

```text
Loading conversation...
```

### Streaming

```text
GrowthGuide
Ollama · gemma3:4b

Generating...
```

### Loading providers

The provider selector can remain disabled until provider information is available.

---

# 22. Error States

Errors should be clear, concise, and actionable.

Example:

```text
Unable to generate a response.

Please try again.
```

For infrastructure-related failures, the UI should avoid exposing internal stack traces.

The retry action should remain available when appropriate.

---

# 23. Empty State

When a new conversation has no messages, the chat should provide a simple starting point and keep the input immediately available.

Example:

```text
                 GrowthGuide

        Ask about product and growth.

    Explore Lenny's podcast knowledge,
       strategies, and practical ideas.

┌───────────────────────────────────────┐
│ Ask GrowthGuide anything...           │
└───────────────────────────────────────┘
```

The empty state should remain lightweight rather than becoming a dashboard.

---

# 24. Out-of-Domain Responses

When the assistant cannot ground a knowledge question in the available transcript data, the response should clearly communicate that limitation.

The UI should treat this as a normal assistant response rather than an application error.

No unrelated source cards should be shown.

---

# 25. Accessibility

The interface should support:

* Keyboard navigation
* Visible focus states
* Semantic buttons
* Accessible labels for icon-only controls
* Sufficient text contrast
* Logical heading hierarchy
* Screen-reader-friendly status updates
* Usable controls on smaller screens

Important actions such as:

* New chat
* Send
* Edit
* Retry
* Copy
* View artifact
* Close artifact

must be accessible without relying only on visual icons.

---

# 26. Content Design

The assistant should provide concise, readable responses.

For longer responses:

* Use headings
* Use short paragraphs
* Use lists where appropriate
* Avoid unnecessary repetition
* Keep citations visually separate

The UI should allow long-form content without making every response appear visually heavy.

---

# 27. Ship 30 for 30 Presentation

Ship 30 for 30 content should be treated as a long-form writing artifact.

The presentation should support:

* Strong opening hook
* Clear central thesis
* Short sections
* Descriptive headings
* Practical examples
* Relevant supporting evidence
* Clear conclusion

The artifact viewer is preferred for long-form generated essays so the chat remains compact.

---

# 28. Edit and Retry UX

### Editing a message

1. User selects `Edit`.
2. Message becomes editable.
3. User changes the content.
4. User selects `Save & retry`.
5. Later conversation state is replaced.
6. New assistant response is generated.

### Retrying a response

1. User selects `Retry`.
2. Existing assistant response enters a loading state.
3. The response is regenerated using the conversation history.
4. The new response replaces the previous result.

The UI should clearly indicate when these operations are in progress.

---

# 29. Copy Interaction

Messages should provide a copy action for convenient reuse.

After copying, the interface can provide lightweight confirmation:

```text
Copied
```

The confirmation should not interrupt the conversation.

---

# 30. Visual Design Principles

The visual system follows these principles:

### Hierarchy

The conversation is the primary focus.

### Restraint

Avoid unnecessary cards, badges, gradients, or decorative elements.

### Consistency

Buttons, spacing, typography, and states should behave consistently across the application.

### Context

Controls should appear close to the content they affect.

### Feedback

Actions should provide immediate visual feedback.

### Readability

Long assistant responses and artifacts should remain comfortable to scan.

---

# 31. Interaction Principles

The application should follow these interaction rules:

1. A new conversation should be one click away.
2. Switching sessions should never mix histories.
3. Sending a message should provide immediate feedback.
4. Streaming should visibly communicate progress.
5. Sources should be easy to distinguish from generated text.
6. Artifacts should be opened intentionally.
7. HTML artifacts should remain isolated.
8. Errors should be understandable.
9. Retry should be available when generation fails.
10. Editing should preserve the user's conversational intent.

---

# 32. Manual UI Validation

Before final delivery, validate the following:

### Conversations

* Create a new conversation.
* Send multiple messages.
* Refresh the browser.
* Confirm the conversation persists.
* Switch between sessions.
* Confirm histories remain independent.

### Chat

* Send a normal question.
* Send a conversational greeting.
* Confirm streaming works.
* Confirm provider/model information appears.
* Confirm errors are understandable.

### Sources

* Ask a knowledge question.
* Confirm relevant sources appear.
* Confirm conversational messages do not show unrelated sources.

### Edit / Retry

* Edit a user message.
* Save and regenerate.
* Retry an assistant response.
* Confirm later conversation state is handled correctly.

### Artifacts

* Generate a Markdown artifact.
* Open it from its assistant message.
* Close the viewer.
* Generate an HTML artifact.
* Confirm it renders inside the isolated viewer.

### Responsive

* Test desktop.
* Test tablet-sized viewport.
* Test mobile-sized viewport.
* Confirm sidebar and artifact viewer remain usable.

### Accessibility

* Navigate important controls using the keyboard.
* Confirm buttons have meaningful labels.
* Confirm focus remains understandable.
* Confirm content remains readable at smaller widths.

---

# 33. Design Trade-offs

## Two-Column Workspace

A dedicated artifact area improves long-form content consumption but reduces chat width when open.

**Decision:** Keep the artifact viewer contextual and closed by default.

## Provider Selector in Input

Placing provider selection inside the input keeps the application header simple.

**Decision:** Show provider/model selection where the user sends the request.

## Explicit Artifact Opening

Automatically opening artifacts could interrupt normal conversation.

**Decision:** Attach artifacts to messages and require an explicit `View artifact` action.

## Local-First Interface

Local Ollama availability can vary by machine.

**Decision:** Clearly communicate provider availability and allow configured providers to be selected.

---

# 34. Final UX Goal

The final experience should feel like a focused growth research assistant, not a generic AI dashboard.

The intended interaction is:

```text
Open GrowthGuide
      │
      ▼
Choose / create conversation
      │
      ▼
Ask a growth question
      │
      ▼
See grounded streaming response
      │
      ├── Sources
      │
      └── Artifact, if generated
               │
               ▼
        Open artifact when needed
```

The interface should remain simple, fast, readable, and predictable throughout this flow.