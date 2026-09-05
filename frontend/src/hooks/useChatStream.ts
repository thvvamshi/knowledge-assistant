"use client";

import {
  useCallback,
  useRef,
  useState,
} from "react";

import {
  Message,
  Provider,
  SourceCitation,
} from "@/lib/api";

import {
  Artifact,
  shouldGenerateArtifact,
} from "@/lib/artifact";

interface UseChatStreamOptions {
  sessionId: string | null;
  provider: Provider;

  onMessage: (
    message: Message,
  ) => void;

  onArtifact: (
    artifact: Artifact,
    messageId: string,
  ) => void;
}

interface StreamArtifact {
  type?: "markdown" | "html";
  title?: string;
  content?: string;
}

interface StreamEvent {
  type?: string;

  /*
   * Token events use `content`.
   */
  content?: string;

  /*
   * Complete events from the backend use `answer`.
   */
  answer?: string;

  provider?: string;
  model?: string;
  sources?: SourceCitation[];

  artifact?: StreamArtifact | null;

  /*
   * Kept for compatibility with older backend event shapes.
   */
  artifact_content?: string;
  artifact_type?: "markdown" | "html";
  artifact_provider?: string;
  artifact_model?: string;

  message?: string;
  code?: string;
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://localhost:8000";

export function useChatStream({
  sessionId,
  provider,
  onMessage,
  onArtifact,
}: UseChatStreamOptions) {
  const [streaming, setStreaming] =
    useState(false);

  const [error, setError] =
    useState("");

  /*
   * React state updates are asynchronous.
   *
   * This ref provides a synchronous lock so rapid
   * clicks or Enter presses cannot start multiple
   * requests before `streaming` becomes true.
   */
  const streamingRef =
    useRef(false);

  /*
   * Each request gets an ID.
   *
   * If a request becomes stale because the session
   * changes, events from that old request are ignored.
   */
  const requestIdRef =
    useRef(0);

  const sendMessage =
    useCallback(
      async (
        content: string,
      ) => {
        const trimmed =
          content.trim();

        /*
         * First synchronous guard.
         */
        if (
          !sessionId ||
          !trimmed ||
          streamingRef.current
        ) {
          return;
        }

        /*
         * Lock immediately.
         */
        streamingRef.current =
          true;

        setStreaming(true);
        setError("");

        const requestId =
          ++requestIdRef.current;

        const assistantMessageId =
          crypto.randomUUID();

        const createdAt =
          new Date().toISOString();

        let assistantContent =
          "";

        let responseProvider:
          string | null = null;

        let responseModel:
          string | null = null;

        let sources: SourceCitation[] =
          [];

        let completed = false;

        const isCurrentRequest =
          () =>
            requestId ===
            requestIdRef.current;

        /*
         * Emit the current assistant state.
         *
         * The page merges messages by ID, so every
         * streaming token updates the same assistant
         * message instead of creating duplicates.
         */
        const emitAssistantMessage =
          () => {
            if (
              !isCurrentRequest()
            ) {
              return;
            }

            onMessage({
              id: assistantMessageId,
              session_id:
                sessionId,
              role: "assistant",
              content:
                assistantContent,
              provider:
                responseProvider,
              model:
                responseModel,
              sources,
              created_at:
                createdAt,
            });
          };

        const generateArtifact =
          shouldGenerateArtifact(
            trimmed,
          );

        try {
          const response =
            await fetch(
              `${API_BASE_URL}/api/chat`,
              {
                method: "POST",
                headers: {
                  "Content-Type":
                    "application/json",
                },
                body: JSON.stringify({
                  session_id:
                    sessionId,
                  content: trimmed,
                  provider,
                  generate_artifact:
                    generateArtifact,
                }),
              },
            );

          if (!response.ok) {
            const errorBody =
              await response
                .json()
                .catch(() => null);

            throw new Error(
              errorBody?.message ??
                errorBody?.detail
                  ?.message ??
                errorBody?.detail ??
                `Request failed with status ${response.status}.`,
            );
          }

          if (!response.body) {
            throw new Error(
              "The assistant returned an empty response.",
            );
          }

          const reader =
            response.body.getReader();

          const decoder =
            new TextDecoder();

          let buffer = "";

          /*
           * Process one NDJSON event.
           */
          const processEvent =
            (
              event: StreamEvent,
            ) => {
              if (
                !isCurrentRequest()
              ) {
                return;
              }

              switch (
                event.type
              ) {
                case "metadata": {
                  responseProvider =
                    event.provider ??
                    responseProvider;

                  responseModel =
                    event.model ??
                    responseModel;

                  emitAssistantMessage();

                  break;
                }

                case "sources": {
                  sources =
                    event.sources ??
                    [];

                  emitAssistantMessage();

                  break;
                }

                case "token": {
                  assistantContent +=
                    event.content ??
                    "";

                  emitAssistantMessage();

                  break;
                }

                case "artifact": {
                  /*
                   * Current backend shape:
                   *
                   * {
                   *   type: "artifact",
                   *   artifact: {
                   *     type,
                   *     title,
                   *     content
                   *   }
                   * }
                   */

                  if (
                    event.artifact?.content
                  ) {
                    onArtifact(
                      {
                        type:
                          event.artifact
                            .type ??
                          "markdown",
                        title:
                          event.artifact
                            .title ??
                          "Generated Artifact",
                        content:
                          event.artifact
                            .content,
                      },
                      assistantMessageId,
                    );

                    break;
                  }

                  /*
                   * Compatibility with the older
                   * artifact event shape.
                   */
                  if (
                    event.artifact_content
                  ) {
                    onArtifact(
                      {
                        type:
                          event.artifact_type ??
                          "markdown",
                        title:
                          "Generated Artifact",
                        content:
                          event.artifact_content,
                      },
                      assistantMessageId,
                    );
                  }

                  break;
                }

                case "complete": {
                  completed = true;

                  /*
                   * IMPORTANT:
                   *
                   * The backend's current complete event
                   * uses `answer`, not `content`.
                   *
                   * Prefer the final normalized answer.
                   */
                  if (
                    typeof event.answer ===
                    "string"
                  ) {
                    assistantContent =
                      event.answer;
                  } else if (
                    typeof event.content ===
                    "string"
                  ) {
                    /*
                     * Backward compatibility.
                     */
                    assistantContent =
                      event.content;
                  }

                  responseProvider =
                    event.provider ??
                    responseProvider;

                  responseModel =
                    event.model ??
                    responseModel;

                  sources =
                    event.sources ??
                    sources;

                  /*
                   * Current backend sends the artifact
                   * as an object in the complete event.
                   */
                  if (
                    event.artifact?.content
                  ) {
                    onArtifact(
                      {
                        type:
                          event.artifact
                            .type ??
                          "markdown",
                        title:
                          event.artifact
                            .title ??
                          "Generated Artifact",
                        content:
                          event.artifact
                            .content,
                      },
                      assistantMessageId,
                    );
                  } else if (
                    event.artifact_content
                  ) {
                    /*
                     * Backward compatibility with the
                     * older artifact event shape.
                     */
                    onArtifact(
                      {
                        type:
                          event.artifact_type ??
                          "markdown",
                        title:
                          "Generated Artifact",
                        content:
                          event.artifact_content,
                      },
                      assistantMessageId,
                    );
                  }

                  /*
                   * Emit one final message using the
                   * authoritative complete event.
                   *
                   * This replaces the streamed content
                   * with the backend-normalized content.
                   */
                  emitAssistantMessage();

                  break;
                }

                case "error": {
                  throw new Error(
                    event.message ??
                      "The assistant returned an error.",
                  );
                }

                default: {
                  /*
                   * Ignore unknown event types so the
                   * frontend remains forward-compatible.
                   */
                  break;
                }
              }
            };

          /*
           * Read the streaming response.
           */
          while (true) {
            const {
              value,
              done,
            } = await reader.read();

            if (done) {
              break;
            }

            buffer +=
              decoder.decode(
                value,
                {
                  stream: true,
                },
              );

            const lines =
              buffer.split("\n");

            /*
             * The final item may be incomplete.
             * Keep it in `buffer` for the next chunk.
             */
            buffer =
              lines.pop() ?? "";

            for (const line of lines) {
              const trimmedLine =
                line.trim();

              if (
                !trimmedLine
              ) {
                continue;
              }

              try {
                const event: StreamEvent =
                  JSON.parse(
                    trimmedLine,
                  );

                processEvent(event);
              } catch (parseError) {
                /*
                 * Errors intentionally thrown from
                 * processEvent("error") must propagate.
                 */
                if (
                  parseError instanceof
                    Error &&
                  parseError.message.includes(
                    "The assistant returned an error.",
                  )
                ) {
                  throw parseError;
                }

                /*
                 * Do not terminate the entire response because
                 * of one malformed/unknown NDJSON line.
                 */
                console.warn(
                  "Ignoring invalid stream event:",
                  trimmedLine,
                  parseError,
                );
              }
            }
          }

          /*
           * Flush TextDecoder in case the final UTF-8
           * characters were still buffered internally.
           */
          buffer +=
            decoder.decode();

          const remaining =
            buffer.trim();

          if (remaining) {
            try {
              const event: StreamEvent =
                JSON.parse(
                  remaining,
                );

              processEvent(event);
            } catch (parseError) {
              if (
                parseError instanceof
                  Error &&
                parseError.message.includes(
                  "The assistant returned an error.",
                )
              ) {
                throw parseError;
              }

              console.warn(
                "Ignoring incomplete trailing stream event:",
                parseError,
              );
            }
          }

          /*
           * A successful backend stream must eventually
           * send a complete event.
           */
          if (
            !completed &&
            isCurrentRequest()
          ) {
            throw new Error(
              "The assistant response ended unexpectedly.",
            );
          }
        } catch (err) {
          /*
           * Ignore errors from stale requests.
           */
          if (
            !isCurrentRequest()
          ) {
            return;
          }

          const message =
            err instanceof
              Error
              ? err.message
              : "The assistant is temporarily unavailable.";

          setError(
            message,
          );
        } finally {
          /*
           * Only the active request can release the lock.
           */
          if (
            isCurrentRequest()
          ) {
            streamingRef.current =
              false;

            setStreaming(false);
          }
        }
      },
      [
        sessionId,
        provider,
        onMessage,
        onArtifact,
      ],
    );

  return {
    sendMessage,
    streaming,
    error,
  };
}