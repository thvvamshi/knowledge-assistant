"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { Message } from "@/lib/api";

interface MessageItemProps {
  message: Message;
  disabled?: boolean;
  editing?: boolean;
  editValue?: string;

  onEditStart?: (
    message: Message,
  ) => void;

  onEditChange?: (
    value: string,
  ) => void;

  onEditCancel?: () => void;

  onEditSave?: () => void;

  onRetry?: (
    message: Message,
  ) => void;

  onOpenArtifact?: (
    message: Message,
  ) => void;
}

async function copyText(
  text: string,
): Promise<boolean> {
  if (!text.trim()) {
    return false;
  }

  try {
    await navigator.clipboard.writeText(text);

    return true;
  } catch {
    try {
      const textarea =
        document.createElement("textarea");

      textarea.value = text;
      textarea.setAttribute("readonly", "");

      textarea.style.position = "fixed";
      textarea.style.left = "-9999px";
      textarea.style.opacity = "0";

      document.body.appendChild(textarea);

      textarea.focus();
      textarea.select();

      const success =
        document.execCommand("copy");

      textarea.remove();

      return success;
    } catch {
      return false;
    }
  }
}

function getProviderLabel(
  message: Message,
): string | null {
  const provider =
    message.provider?.trim() ?? "";

  const model =
    message.model?.trim() ?? "";

  if (!provider && !model) {
    return null;
  }

  if (provider && model) {
    return `${provider} · ${model}`;
  }

  return provider || model;
}

function ActionButton({
  children,
  onClick,
  disabled,
  label,
}: {
  children: React.ReactNode;
  onClick: () => void;
  disabled?: boolean;
  label: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-label={label}
      className="rounded-md px-2 py-1 text-[10px] text-neutral-600 transition hover:bg-neutral-900 hover:text-neutral-300 disabled:cursor-not-allowed disabled:opacity-30"
    >
      {children}
    </button>
  );
}

export function MessageItem({
  message,
  disabled = false,
  editing = false,
  editValue = "",
  onEditStart,
  onEditChange,
  onEditCancel,
  onEditSave,
  onRetry,
  onOpenArtifact,
}: MessageItemProps) {
  const [copied, setCopied] =
    useState(false);

  const isUser =
    message.role === "user";

  const providerLabel =
    getProviderLabel(message);

  const handleCopy = async () => {
    if (disabled) {
      return;
    }

    const success = await copyText(
      message.content,
    );

    if (!success) {
      return;
    }

    setCopied(true);

    window.setTimeout(() => {
      setCopied(false);
    }, 1500);
  };

  /*
   * User messages can be edited.
   */
  if (isUser) {
    return (
      <div className="flex flex-col items-end gap-2">
        {editing ? (
          <div className="w-full max-w-2xl">
            <div className="overflow-hidden rounded-2xl border border-neutral-700 bg-neutral-900">
              <textarea
                value={editValue}
                onChange={(event) =>
                  onEditChange?.(
                    event.target.value,
                  )
                }
                disabled={disabled}
                autoFocus
                rows={4}
                aria-label="Edit message"
                className="w-full resize-none bg-transparent px-4 py-3 text-sm leading-6 text-neutral-200 outline-none placeholder:text-neutral-600 disabled:cursor-not-allowed disabled:opacity-50"
                onKeyDown={(event) => {
                  if (
                    event.nativeEvent
                      .isComposing
                  ) {
                    return;
                  }

                  if (
                    event.key === "Enter" &&
                    !event.shiftKey
                  ) {
                    event.preventDefault();

                    if (
                      !disabled &&
                      editValue.trim()
                    ) {
                      onEditSave?.();
                    }
                  }

                  if (
                    event.key === "Escape"
                  ) {
                    event.preventDefault();
                    onEditCancel?.();
                  }
                }}
              />

              <div className="flex items-center justify-end gap-2 border-t border-neutral-800 px-3 py-2">
                <button
                  type="button"
                  onClick={onEditCancel}
                  disabled={disabled}
                  className="rounded-lg px-3 py-1.5 text-xs text-neutral-500 transition hover:bg-neutral-800 hover:text-neutral-200 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Cancel
                </button>

                <button
                  type="button"
                  onClick={onEditSave}
                  disabled={
                    disabled ||
                    !editValue.trim()
                  }
                  className="rounded-lg bg-white px-3 py-1.5 text-xs font-medium text-neutral-950 transition hover:bg-neutral-200 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Save & retry
                </button>
              </div>
            </div>
          </div>
        ) : (
          <>
            <div className="max-w-[85%] rounded-2xl bg-white px-4 py-3 text-sm leading-6 text-neutral-950 sm:max-w-2xl">
              <p className="whitespace-pre-wrap break-words">
                {message.content}
              </p>
            </div>

            <div className="flex items-center gap-1 pr-1">
              <ActionButton
                onClick={handleCopy}
                disabled={disabled}
                label="Copy message"
              >
                {copied
                  ? "Copied"
                  : "Copy"}
              </ActionButton>

              <ActionButton
                onClick={() =>
                  onEditStart?.(
                    message,
                  )
                }
                disabled={disabled}
                label="Edit message"
              >
                Edit
              </ActionButton>
            </div>
          </>
        )}
      </div>
    );
  }

  /*
   * Assistant messages cannot be edited.
   * Retry remains available.
   */
  return (
    <div className="group flex items-start gap-3">
      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border border-neutral-800 bg-neutral-900 text-[10px] font-semibold text-neutral-400">
        G
      </div>

      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-medium text-neutral-300">
            GrowthGuide
          </span>

          {providerLabel && (
            <span className="rounded-md border border-neutral-800 bg-neutral-900 px-1.5 py-0.5 text-[9px] text-neutral-600">
              {providerLabel}
            </span>
          )}
        </div>

        <div className="mt-2 max-w-3xl text-sm leading-7 text-neutral-300">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              p: ({ children }) => (
                <p className="mb-4 last:mb-0">
                  {children}
                </p>
              ),

              h1: ({ children }) => (
                <h1 className="mb-4 mt-6 text-xl font-semibold tracking-tight text-white first:mt-0">
                  {children}
                </h1>
              ),

              h2: ({ children }) => (
                <h2 className="mb-3 mt-6 text-lg font-semibold text-white first:mt-0">
                  {children}
                </h2>
              ),

              h3: ({ children }) => (
                <h3 className="mb-2 mt-5 text-base font-semibold text-neutral-200 first:mt-0">
                  {children}
                </h3>
              ),

              ul: ({ children }) => (
                <ul className="mb-4 list-disc space-y-1.5 pl-6">
                  {children}
                </ul>
              ),

              ol: ({ children }) => (
                <ol className="mb-4 list-decimal space-y-1.5 pl-6">
                  {children}
                </ol>
              ),

              li: ({ children }) => (
                <li className="pl-1">
                  {children}
                </li>
              ),

              strong: ({ children }) => (
                <strong className="font-semibold text-white">
                  {children}
                </strong>
              ),

              em: ({ children }) => (
                <em className="text-neutral-200">
                  {children}
                </em>
              ),

              blockquote: ({
                children,
              }) => (
                <blockquote className="my-4 border-l-2 border-neutral-700 pl-4 text-neutral-400">
                  {children}
                </blockquote>
              ),

              hr: () => (
                <hr className="my-6 border-neutral-800" />
              ),

              a: ({
                href,
                children,
              }) => (
                <a
                  href={href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-neutral-200 underline decoration-neutral-700 underline-offset-2 transition hover:decoration-neutral-300"
                >
                  {children}
                </a>
              ),

              code: ({
                className,
                children,
              }) => {
                const isBlock =
                  Boolean(
                    className?.includes(
                      "language-",
                    ),
                  );

                if (isBlock) {
                  return (
                    <code
                      className={`${className ?? ""} font-mono text-xs leading-6 text-neutral-300`}
                    >
                      {children}
                    </code>
                  );
                }

                return (
                  <code className="rounded-md border border-neutral-800 bg-neutral-900 px-1.5 py-0.5 font-mono text-xs text-neutral-300">
                    {children}
                  </code>
                );
              },

              pre: ({ children }) => (
                <pre className="my-4 overflow-x-auto rounded-xl border border-neutral-800 bg-black p-4 font-mono text-xs leading-6">
                  {children}
                </pre>
              ),
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>

        {message.sources.length > 0 && (
          <div className="mt-5 max-w-3xl border-t border-neutral-800 pt-3">
            <div className="mb-2 text-[10px] font-medium uppercase tracking-wide text-neutral-500">
              Sources
            </div>

            <div className="space-y-2">
              {message.sources.map(
                (source, index) => (
                  <div
                    key={`${source.episode_title}-${index}`}
                    className="rounded-lg border border-neutral-800 bg-neutral-900/50 px-3 py-2.5"
                  >
                    <div className="text-xs font-medium text-neutral-300">
                      {source.episode_title}
                    </div>

                    {source.guest_name && (
                      <div className="mt-1 text-[10px] text-neutral-500">
                        {source.guest_name}
                      </div>
                    )}

                    {source.timestamp && (
                      <div className="mt-1 text-[10px] text-neutral-500">
                        {source.timestamp}
                      </div>
                    )}

                    {source.url && (
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mt-1.5 inline-block text-[10px] font-medium text-neutral-400 underline underline-offset-2 transition hover:text-neutral-200"
                      >
                        Open episode →
                      </a>
                    )}
                  </div>
                ),
              )}
            </div>
          </div>
        )}

        {message.artifact && (
          <button
            type="button"
            onClick={() =>
              onOpenArtifact?.(
                message,
              )
            }
            disabled={disabled}
            className="mt-4 flex w-full max-w-md items-center justify-between rounded-xl border border-neutral-800 bg-neutral-900/60 px-4 py-3 text-left transition hover:border-neutral-700 hover:bg-neutral-900 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <div className="min-w-0">
              <div className="truncate text-xs font-medium text-neutral-300">
                {message.artifact.title ||
                  "Generated artifact"}
              </div>

              <div className="mt-1 text-[10px] text-neutral-600">
                {message.artifact.type ===
                "html"
                  ? "HTML document"
                  : "Markdown document"}
              </div>
            </div>

            <span className="ml-4 shrink-0 text-xs text-neutral-500">
              View artifact →
            </span>
          </button>
        )}

        <div className="mt-2 flex items-center gap-1">
          <ActionButton
            onClick={handleCopy}
            disabled={disabled}
            label="Copy response"
          >
            {copied
              ? "Copied"
              : "Copy"}
          </ActionButton>

          <button
            type="button"
            disabled
            aria-label="Editing assistant responses is not allowed"
            className="cursor-not-allowed rounded-md px-2 py-1 text-[10px] text-red-500/70"
          >
            Not allowed to edit
          </button>

          <ActionButton
            onClick={() =>
              onRetry?.(message)
            }
            disabled={disabled}
            label="Retry response"
          >
            Retry
          </ActionButton>
        </div>
      </div>
    </div>
  );
}