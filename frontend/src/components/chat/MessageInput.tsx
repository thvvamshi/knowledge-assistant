"use client";

import { FormEvent } from "react";

import {
  Provider,
  ProvidersResponse,
  Session,
} from "@/lib/api";

interface MessageInputProps {
  input: string;
  loading: boolean;
  session: Session | null;
  provider: Provider;
  providers: ProvidersResponse | null;
  fallbackModel?: string | null;

  onProviderChange: (
    provider: Provider,
  ) => void;

  onInputChange: (
    value: string,
  ) => void;

  onSubmit: (
    event: FormEvent<HTMLFormElement>,
  ) => void;
}

export function MessageInput({
  input,
  loading,
  session,
  provider,
  providers,
  fallbackModel,
  onProviderChange,
  onInputChange,
  onSubmit,
}: MessageInputProps) {
  const disabled = loading || !session;

  const availableProviders =
    providers?.providers.filter(
      (item) =>
        item.configured &&
        item.available,
    ) ?? [];

  const selectedProvider =
    availableProviders.find(
      (item) => item.id === provider,
    ) ?? null;

  const displayProvider =
    selectedProvider?.name ??
    provider;

  const displayModel =
    selectedProvider?.model ??
    fallbackModel ??
    null;

  const handleSubmit = (
    event: FormEvent<HTMLFormElement>,
  ) => {
    if (
      disabled ||
      !input.trim()
    ) {
      event.preventDefault();
      return;
    }

    onSubmit(event);
  };

  const handleProviderChange = (
    event: React.ChangeEvent<HTMLSelectElement>,
  ) => {
    const nextProvider =
      event.target.value as Provider;

    onProviderChange(nextProvider);
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="mx-auto max-w-3xl"
      aria-busy={loading}
    >
      <div
        className={`overflow-hidden rounded-2xl border bg-neutral-900 shadow-sm transition ${
          disabled
            ? "border-neutral-800"
            : "border-neutral-700 focus-within:border-neutral-500"
        }`}
      >
        <textarea
          value={input}
          onChange={(event) =>
            onInputChange(
              event.target.value,
            )
          }
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
                input.trim()
              ) {
                event.currentTarget.form?.requestSubmit();
              }
            }
          }}
          placeholder={
            !session
              ? "Select a conversation..."
              : loading
                ? "Generating response..."
                : "Ask anything..."
          }
          rows={3}
          disabled={disabled}
          aria-label="Message"
          className="min-h-20 w-full resize-none bg-transparent px-4 py-3 text-sm leading-6 text-neutral-200 outline-none placeholder:text-neutral-600 disabled:cursor-not-allowed disabled:opacity-60"
        />

        <div className="flex items-center justify-between gap-3 px-3 pb-2.5">
          <div className="min-w-0">
            {availableProviders.length > 0 ? (
              <label
                htmlFor="message-provider"
                className="block"
              >
                <span className="sr-only">
                  AI provider
                </span>

                <select
                  id="message-provider"
                  value={
                    selectedProvider?.id ??
                    availableProviders[0]?.id ??
                    provider
                  }
                  onChange={
                    handleProviderChange
                  }
                  disabled={disabled}
                  className="max-w-[280px] cursor-pointer appearance-none rounded-lg border border-neutral-800 bg-neutral-950 px-2.5 py-1.5 text-[11px] text-neutral-500 outline-none transition hover:border-neutral-700 hover:text-neutral-300 focus:border-neutral-600 focus:text-neutral-300 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {availableProviders.map(
                    (item) => (
                      <option
                        key={item.id}
                        value={item.id}
                      >
                        {item.name} ·{" "}
                        {item.model}
                      </option>
                    ),
                  )}
                </select>
              </label>
            ) : (
              <div
                className="rounded-lg border border-neutral-800 bg-neutral-950 px-2.5 py-1.5 text-[11px] text-neutral-500"
                title="No configured AI provider is currently available"
              >
                {displayProvider}

                {displayModel
                  ? ` · ${displayModel}`
                  : ""}
              </div>
            )}
          </div>

          <button
            type="submit"
            disabled={
              disabled ||
              !input.trim()
            }
            aria-label={
              loading
                ? "Generating response"
                : "Send message"
            }
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white text-sm font-semibold text-neutral-950 transition hover:bg-neutral-200 disabled:cursor-not-allowed disabled:opacity-30"
          >
            {loading ? (
              <span
                className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-neutral-400 border-t-neutral-950"
                aria-hidden="true"
              />
            ) : (
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                className="h-4 w-4"
                aria-hidden="true"
              >
                <path
                  d="M12 19V5"
                  strokeLinecap="round"
                />
                <path
                  d="m6.5 10.5 5.5-5.5 5.5 5.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            )}
          </button>
        </div>
      </div>

      <div className="mt-2 flex items-center justify-center gap-2 text-[10px] text-neutral-700">
        {loading ? (
          <span>
            Generating response...
          </span>
        ) : (
          <>
            <span>
              Enter to send
            </span>

            <span>·</span>

            <span>
              Shift + Enter for new line
            </span>
          </>
        )}
      </div>
    </form>
  );
}