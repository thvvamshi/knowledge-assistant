"use client";

import { FormEvent, useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  createSession,
  getMessages,
  getProviders,
  Message,
  Provider,
  ProvidersResponse,
  sendMessage,
  Session,
} from "@/lib/api";

export default function Home() {
  const [session, setSession] = useState<Session | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [providers, setProviders] = useState<ProvidersResponse | null>(null);
  const [provider, setProvider] = useState<Provider>("ollama");
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [initializing, setInitializing] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function initialize() {
      try {
        const [newSession, providerData] = await Promise.all([
          createSession("Lenny Growth Assistant"),
          getProviders(),
        ]);

        setSession(newSession);
        setProviders(providerData);
        setProvider(providerData.default_provider);

        const existingMessages = await getMessages(newSession.id);
        setMessages(existingMessages);
      } catch {
        setError(
          "Unable to connect to the assistant. Make sure the backend is running.",
        );
      } finally {
        setInitializing(false);
      }
    }

    initialize();
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const content = input.trim();

    if (!content || !session || loading) {
      return;
    }

    setError("");
    setInput("");
    setLoading(true);

    try {
      const userMessage: Message = {
        id: crypto.randomUUID(),
        session_id: session.id,
        role: "user",
        content,
        provider: null,
        model: null,
        sources: [],
        created_at: new Date().toISOString(),
      };

      setMessages((current) => [...current, userMessage]);

      const assistantMessage = await sendMessage(
        session.id,
        content,
        provider,
      );

      setMessages((current) => [...current, assistantMessage]);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "The assistant is temporarily unavailable.",
      );
    } finally {
      setLoading(false);
    }
  }

  if (initializing) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-neutral-950 text-white">
        <div className="text-sm text-neutral-400">
          Starting Lenny Growth Assistant...
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-neutral-950 text-white">
      <div className="mx-auto flex min-h-screen max-w-7xl flex-col">
        <header className="flex items-center justify-between border-b border-neutral-800 px-6 py-4">
          <div>
            <h1 className="text-lg font-semibold">
              Lenny Growth Assistant
            </h1>
            <p className="text-xs text-neutral-500">
              Grounded in Lenny&apos;s Podcast transcripts
            </p>
          </div>

          <div className="flex items-center gap-3">
            <label
              htmlFor="provider"
              className="text-xs text-neutral-500"
            >
              Provider
            </label>

            <select
              id="provider"
              value={provider}
              onChange={(event) =>
                setProvider(event.target.value as Provider)
              }
              className="rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-2 text-sm outline-none"
            >
              {providers?.providers.map((item) => (
                <option
                  key={item.id}
                  value={item.id}
                  disabled={!item.available}
                >
                  {item.name} — {item.model}
                  {!item.available ? " (unavailable)" : ""}
                </option>
              ))}
            </select>
          </div>
        </header>

        <section className="flex flex-1 flex-col">
          <div className="flex-1 overflow-y-auto px-6 py-8">
            <div className="mx-auto max-w-3xl space-y-6">
              {messages.length === 0 && (
                <div className="py-20 text-center">
                  <h2 className="text-2xl font-semibold">
                    Ask Lenny about growth
                  </h2>
                  <p className="mx-auto mt-3 max-w-lg text-sm leading-6 text-neutral-500">
                    Ask about product strategy, growth, onboarding,
                    retention, leadership, or other topics covered in
                    the podcast transcripts.
                  </p>
                </div>
              )}

              {messages.map((message) => (
                <article
                  key={message.id}
                  className={
                    message.role === "user"
                      ? "ml-auto max-w-2xl"
                      : "max-w-3xl"
                  }
                >
                  <div
                    className={
                      message.role === "user"
                        ? "rounded-2xl bg-white px-5 py-4 text-sm text-neutral-900"
                        : "rounded-2xl border border-neutral-800 bg-neutral-900 px-5 py-4"
                    }
                  >
                    {message.role === "assistant" ? (
                      <div className="prose prose-invert max-w-none text-sm">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {message.content}
                        </ReactMarkdown>
                      </div>
                    ) : (
                      <p className="whitespace-pre-wrap">
                        {message.content}
                      </p>
                    )}
                  </div>

                  {message.role === "assistant" &&
                    message.sources.length > 0 && (
                      <div className="mt-3 rounded-xl border border-neutral-800 bg-neutral-950 p-4">
                        <p className="mb-2 text-xs font-medium text-neutral-400">
                          Sources
                        </p>

                        <div className="space-y-2">
                          {message.sources.map((source, index) => (
                            <a
                              key={`${source.episode_title}-${index}`}
                              href={source.url ?? "#"}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="block text-xs text-neutral-500 hover:text-white"
                            >
                              <span className="font-medium text-neutral-300">
                                {source.episode_title}
                              </span>

                              {source.guest_name && (
                                <span>
                                  {" "}
                                  — {source.guest_name}
                                </span>
                              )}

                              {source.timestamp && (
                                <span>
                                  {" "}
                                  · {source.timestamp}
                                </span>
                              )}
                            </a>
                          ))}
                        </div>
                      </div>
                    )}
                </article>
              ))}

              {loading && (
                <div className="rounded-2xl border border-neutral-800 bg-neutral-900 px-5 py-4 text-sm text-neutral-500">
                  Lenny is thinking...
                </div>
              )}

              {error && (
                <div className="rounded-xl border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
                  {error}
                </div>
              )}
            </div>
          </div>

          <div className="border-t border-neutral-800 px-6 py-5">
            <form
              onSubmit={handleSubmit}
              className="mx-auto flex max-w-3xl gap-3"
            >
              <textarea
                value={input}
                onChange={(event) => setInput(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    event.currentTarget.form?.requestSubmit();
                  }
                }}
                placeholder="Ask a question about Lenny's Podcast..."
                rows={2}
                disabled={loading || !session}
                className="min-h-12 flex-1 resize-none rounded-xl border border-neutral-700 bg-neutral-900 px-4 py-3 text-sm outline-none placeholder:text-neutral-600 focus:border-neutral-500"
              />

              <button
                type="submit"
                disabled={loading || !input.trim() || !session}
                className="self-end rounded-xl bg-white px-5 py-3 text-sm font-medium text-neutral-900 transition hover:bg-neutral-200 disabled:cursor-not-allowed disabled:opacity-40"
              >
                Send
              </button>
            </form>

            <p className="mx-auto mt-2 max-w-3xl text-xs text-neutral-600">
              Answers are grounded in the available transcript library.
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}