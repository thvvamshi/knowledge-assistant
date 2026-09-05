# Agent Transcript 04 — Artifacts and Security

## Objective

Implement generated artifacts while safely handling untrusted model-generated HTML.

## Work Completed

- Added artifact request detection.
- Added Markdown artifact generation.
- Added HTML artifact generation.
- Added artifact persistence.
- Added artifact attachment to assistant messages.
- Added artifact viewing UI.
- Added Markdown rendering.
- Added isolated HTML rendering.

## Artifact Types

The backend supports:

- Markdown artifacts.
- HTML artifacts.

Artifact generation is triggered when the user's request clearly asks for an artifact or document.

## Security Problem

Generated HTML is untrusted model output.

Rendering generated HTML directly inside the main application DOM could allow model-generated markup or scripts to interact with the application.

## Correction

HTML is sanitized using DOMPurify before rendering.

HTML artifacts are rendered inside a sandboxed iframe.

The iframe uses:

sandbox="allow-scripts"

and intentionally does not use:

allow-same-origin

This keeps generated HTML isolated from the application's main origin.

## UX Decision

Artifacts do not automatically open when generated.

Instead, the assistant message displays a "View artifact" action.

The user explicitly chooses when to open the artifact viewer.

The viewer can appear beside the chat on desktop and as a drawer-style view on smaller screens.

## Result

Markdown and HTML artifacts can be generated, persisted, and viewed while generated HTML remains isolated from the main application.
