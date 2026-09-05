"use client";

import {
  FormEvent,
  useEffect,
  useRef,
} from "react";

import {
  Message,
  Provider,
  ProvidersResponse,
  Session,
} from "@/lib/api";

import { MessageInput } from "./MessageInput";
import { MessageItem } from "./MessageItem";

interface ChatPaneProps {
  session: Session | null;
  messages: Message[];
  providers: ProvidersResponse | null;
  provider: Provider;
  input: string;
  loading: boolean;
  error: string;
  sessionLoading: boolean;
  hasStreamingResponse: boolean;

  editingMessageId: string | null;
  editValue: string;

  artifactOpen: boolean;

  onEditStart: (message: Message) => void;
  onEditChange: (value: string) => void;
  onEditCancel: () => void;
  onEditSave: () => void;

  onRetry: (message: Message) => void;

  onOpenArtifact: (message: Message) => void;

  onProviderChange: (provider: Provider) => void;
  onInputChange: (value: string) => void;

  onSubmit: (
    event: FormEvent<HTMLFormElement>,
  ) => void;

  onOpenSidebar: () => void;
}

export function ChatPane({
  session,
  messages,
  providers,
  provider,
  input,
  loading,
  error,
  sessionLoading,
  hasStreamingResponse,
  editingMessageId,
  editValue,
  artifactOpen,
  onEditStart,
  onEditChange,
  onEditCancel,
  onEditSave,
  onRetry,
  onOpenArtifact,
  onProviderChange,
  onInputChange,
  onSubmit,
  onOpenSidebar,
}: ChatPaneProps) {
  const messagesEndRef =
    useRef<HTMLDivElement | null>(null);

  /*
   * Conversation-level busy state.
   *
   * Editing is intentionally excluded because the
   * currently edited message must remain interactive.
   */
  const busy =
    loading ||
    sessionLoading;

  const latestAssistantModel =
    [...messages]
      .reverse()
      .find(
        (message) =>
          message.role === "assistant" &&
          message.model,
      )?.model ?? null;

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: loading ? "auto" : "smooth",
      block: "end",
    });
  }, [messages, loading]);

  return (
    <div className="flex h-full min-h-0 flex-col bg-neutral-950">
      {/* Header */}
      <header className="flex h-14 shrink-0 items-center border-b border-neutral-800 px-3 sm:px-5">
        <div className="flex min-w-0 items-center gap-2">
          <button
            type="button"
            onClick={onOpenSidebar}
            aria-label="Toggle conversations"
            title="Toggle conversations"
            className="flex h-8 w-8 items-center justify-center rounded-lg text-neutral-500 transition hover:bg-neutral-900 hover:text-white focus:outline-none focus:ring-2 focus:ring-neutral-700"
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.7"
              className="h-5 w-5"
              aria-hidden="true"
            >
              <path
                d="M4 7h16M4 12h16M4 17h16"
                strokeLinecap="round"
              />
            </svg>
          </button>

          <h1 className="truncate text-sm font-medium text-neutral-200">
            {session?.title?.trim() &&
            session.title !== "New conversation" &&
            session.title !== "New chat"
              ? session.title
              : "New chat"}
          </h1>
        </div>

        {artifactOpen && (
          <div className="ml-auto hidden items-center gap-2 text-[10px] text-neutral-600 sm:flex">
            <span className="h-1.5 w-1.5 rounded-full bg-neutral-600" />
            Artifact open
          </div>
        )}
      </header>

      {/* Messages */}
      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-8 sm:px-6">
        <div className="mx-auto max-w-3xl space-y-8">
          {sessionLoading && (
            <div className="flex items-center justify-center py-12">
              <div className="flex items-center gap-2 text-xs text-neutral-600">
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-neutral-500" />
                Loading conversation...
              </div>
            </div>
          )}

          {!sessionLoading && messages.length === 0 && (
            <div className="flex min-h-[55vh] items-center justify-center">
              <div className="max-w-lg px-4 text-center">
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl border border-neutral-800 bg-neutral-900 text-sm font-semibold text-neutral-400">
                  G
                </div>

                <h2 className="mt-5 text-2xl font-semibold tracking-tight text-white">
                  What can I help you with?
                </h2>

                <p className="mx-auto mt-3 max-w-md text-sm leading-6 text-neutral-500">
                  Ask about product strategy, growth,
                  onboarding, retention, leadership,
                  or ideas from the available podcast
                  knowledge.
                </p>

                <div className="mt-6 flex flex-wrap justify-center gap-2">
                  {[
                    "How do I improve activation?",
                    "What makes a good growth loop?",
                    "How should I think about retention?",
                  ].map((prompt) => (
                    <button
                      key={prompt}
                      type="button"
                      onClick={() =>
                        onInputChange(prompt)
                      }
                      disabled={busy}
                      className="rounded-full border border-neutral-800 px-3.5 py-2 text-xs text-neutral-500 transition hover:border-neutral-600 hover:bg-neutral-900 hover:text-neutral-300 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {!sessionLoading &&
            messages.map((message) => (
              <MessageItem
                key={message.id}
                message={message}
                disabled={
                  busy &&
                  editingMessageId !== message.id
                }
                editing={
                  editingMessageId === message.id
                }
                editValue={
                  editingMessageId === message.id
                    ? editValue
                    : ""
                }
                onEditStart={onEditStart}
                onEditChange={onEditChange}
                onEditCancel={onEditCancel}
                onEditSave={onEditSave}
                onRetry={onRetry}
                onOpenArtifact={onOpenArtifact}
              />
            ))}

          {/* Thinking indicator */}
          {loading && !hasStreamingResponse && (
            <div className="flex items-start gap-3">
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border border-neutral-800 bg-neutral-900 text-[10px] font-semibold text-neutral-400">
                G
              </div>

              <div className="pt-1">
                <div
                  className="flex items-center gap-2"
                  aria-live="polite"
                  aria-label="Assistant is thinking"
                >
                  <span className="text-xs text-neutral-500">
                    Thinking
                  </span>

                  <span className="flex gap-1">
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-neutral-600 [animation-delay:-0.3s]" />
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-neutral-600 [animation-delay:-0.15s]" />
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-neutral-600" />
                  </span>
                </div>
              </div>
            </div>
          )}

          {error && (
            <div
              role="alert"
              className="rounded-xl border border-red-900/60 bg-red-950/30 px-4 py-3 text-sm text-red-300"
            >
              {error}
            </div>
          )}

          <div
            ref={messagesEndRef}
            aria-hidden="true"
            className="h-px"
          />
        </div>
      </div>

      {/* Input */}
      <div className="shrink-0 px-3 pb-3 pt-2 sm:px-5 sm:pb-5">
        <MessageInput
          input={input}
          loading={
            loading ||
            editingMessageId !== null
          }
          session={session}
          provider={provider}
          providers={providers}
          fallbackModel={latestAssistantModel}
          onProviderChange={onProviderChange}
          onInputChange={onInputChange}
          onSubmit={onSubmit}
        />

        <p className="mx-auto mt-2 max-w-3xl text-center text-[10px] text-neutral-700">
          Responses are grounded in the available
          transcript knowledge.
        </p>
      </div>
    </div>
  );
}