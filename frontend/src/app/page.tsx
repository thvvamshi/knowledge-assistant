"use client";

import {
  FormEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import { useParams, useRouter } from "next/navigation";

import { ArtifactViewer } from "@/components/artifact/ArtifactViewer";
import { ChatPane } from "@/components/chat/ChatPane";
import { Sidebar } from "@/components/sidebar/Sidebar";

import {
  createConversationTitle,
  createSession,
  editMessage,
  getMessages,
  getProviders,
  getSessions,
  retryMessage,
} from "@/lib/api";

import type {
  Message,
  MessageArtifact,
  Provider,
  ProvidersResponse,
  Session,
} from "@/lib/api";

import { useChatStream } from "@/hooks/useChatStream";

export default function HomePage() {
  const router = useRouter();
  const params = useParams();

  const routeSessionId =
    typeof params?.sessionId === "string"
      ? params.sessionId
      : null;

  const [session, setSession] =
    useState<Session | null>(null);

  const [sessions, setSessions] =
    useState<Session[]>([]);

  const [messages, setMessages] =
    useState<Message[]>([]);

  const [providers, setProviders] =
    useState<ProvidersResponse | null>(null);

  const [provider, setProvider] =
    useState<Provider>("ollama");

  const [input, setInput] =
    useState("");

  const [initializing, setInitializing] =
    useState(true);

  const [sessionLoading, setSessionLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  const [selectedArtifact, setSelectedArtifact] =
    useState<MessageArtifact | null>(null);

  const [artifactOpen, setArtifactOpen] =
    useState(false);

  const [sidebarOpen, setSidebarOpen] =
    useState(false);

  const [sidebarCollapsed, setSidebarCollapsed] =
    useState(false);

  const [hasStreamingResponse, setHasStreamingResponse] =
    useState(false);

  const [editingMessageId, setEditingMessageId] =
    useState<string | null>(null);

  const [editValue, setEditValue] =
    useState("");

  const actionLock =
    useRef(false);

  /*
   * Chat stream.
   */
  const {
    sendMessage,
    streaming,
    error: streamError,
  } = useChatStream({
    sessionId:
      session?.id ?? null,

    provider,

    onMessage: (message) => {
      setMessages((current) => {
        const existingIndex =
          current.findIndex(
            (item) =>
              item.id === message.id,
          );

        if (existingIndex === -1) {
          return [
            ...current,
            message,
          ];
        }

        const updated =
          [...current];

        updated[existingIndex] = {
          ...updated[existingIndex],
          ...message,
        };

        return updated;
      });
    },

    onArtifact: (
      artifact,
      messageId,
    ) => {
      setMessages((current) =>
        current.map(
          (message) =>
            message.id === messageId
              ? {
                  ...message,
                  artifact,
                }
              : message,
        ),
      );
    },
  });

  const interactionBusy =
    streaming ||
    sessionLoading;

  /*
   * Recover titles for all sessions.
   *
   * The backend currently creates sessions with
   * "New chat". If a session already has messages,
   * use its first user message as the sidebar title.
   */
  const hydrateSessionTitles =
    useCallback(
      async (
        sessionList: Session[],
      ): Promise<Session[]> => {
        return Promise.all(
          sessionList.map(
            async (
              item,
            ): Promise<Session> => {
              if (
                item.title &&
                item.title
                  .trim()
                  .toLowerCase() !==
                  "new chat"
              ) {
                return item;
              }

              try {
                const sessionMessages =
                  await getMessages(
                    item.id,
                  );

                const firstUserMessage =
                  sessionMessages.find(
                    (message) =>
                      message.role ===
                      "user",
                  );

                if (
                  firstUserMessage?.content
                ) {
                  return {
                    ...item,
                    title:
                      createConversationTitle(
                        firstUserMessage.content,
                      ),
                  };
                }
              } catch {
                /*
                 * Keep the backend title when
                 * messages cannot be loaded.
                 */
              }

              return item;
            },
          ),
        );
      },
      [],
    );

  /*
   * Initialize application.
   */
  useEffect(() => {
    let cancelled = false;

    async function initialize() {
      try {
        const [
          providerData,
          existingSessions,
        ] = await Promise.all([
          getProviders(),
          getSessions(),
        ]);

        if (cancelled) {
          return;
        }

        setProviders(
          providerData,
        );

        /*
         * Select the first configured and
         * available provider.
         */
        const availableProvider =
          providerData.providers.find(
            (item) =>
              item.configured &&
              item.available,
          );

        setProvider(
          availableProvider?.id ??
            providerData.default_provider,
        );

        /*
         * Reconstruct titles for every existing
         * conversation.
         */
        const titledSessions =
          await hydrateSessionTitles(
            existingSessions,
          );

        if (cancelled) {
          return;
        }

        let activeSession:
          | Session
          | null = null;

        /*
         * Prefer the session from the URL.
         */
        if (routeSessionId) {
          activeSession =
            titledSessions.find(
              (item) =>
                item.id ===
                routeSessionId,
            ) ?? null;
        }

        /*
         * If the URL does not contain a valid
         * session, use the newest session.
         */
        if (
          !activeSession &&
          titledSessions.length > 0
        ) {
          activeSession =
            titledSessions[0];
        }

        /*
         * Create the first conversation only
         * when no conversation exists.
         */
        if (!activeSession) {
          activeSession =
            await createSession(
              "New chat",
            );
        }

        if (
          cancelled ||
          !activeSession
        ) {
          return;
        }

        const availableSessions =
          titledSessions.length > 0
            ? titledSessions
            : [activeSession];

        /*
         * Use the titled version of the active
         * session when available.
         */
        const titledActiveSession =
          availableSessions.find(
            (item) =>
              item.id ===
              activeSession!.id,
          );

        if (
          titledActiveSession
        ) {
          activeSession =
            titledActiveSession;
        }

        setSessions(
          availableSessions,
        );

        setSession(
          activeSession,
        );

        /*
         * Make sure the browser URL represents
         * the active conversation.
         */
        const expectedPath =
          `/chat/${activeSession.id}`;

        if (
          window.location.pathname !==
          expectedPath
        ) {
          router.replace(
            expectedPath,
          );
        }

        /*
         * Load messages for the active session.
         */
        const existingMessages =
          await getMessages(
            activeSession.id,
          );

        if (cancelled) {
          return;
        }

        setMessages(
          existingMessages,
        );

        /*
         * Recover the active title if it
         * still says "New chat".
         */
        const firstUserMessage =
          existingMessages.find(
            (message) =>
              message.role ===
              "user",
          );

        if (
          firstUserMessage &&
          (
            !activeSession.title ||
            activeSession.title
              .trim()
              .toLowerCase() ===
              "new chat"
          )
        ) {
          const generatedTitle =
            createConversationTitle(
              firstUserMessage.content,
            );

          setSession(
            (current) =>
              current
                ? {
                    ...current,
                    title:
                      generatedTitle,
                  }
                : current,
          );

          setSessions(
            (current) =>
              current.map(
                (item) =>
                  item.id ===
                  activeSession!.id
                    ? {
                        ...item,
                        title:
                          generatedTitle,
                      }
                    : item,
              ),
          );
        }
      } catch {
        if (!cancelled) {
          setError(
            "Unable to connect to the assistant. Make sure the backend is running.",
          );
        }
      } finally {
        if (!cancelled) {
          setInitializing(
            false,
          );
        }
      }
    }

    void initialize();

    return () => {
      cancelled = true;
    };
  }, [
    routeSessionId,
    router,
    hydrateSessionTitles,
  ]);

  /*
   * Switch conversations.
   */
  async function handleSessionSelect(
    sessionId: string,
  ) {
    if (
      interactionBusy ||
      actionLock.current
    ) {
      return;
    }

    if (
      sessionId === session?.id
    ) {
      setSidebarOpen(false);

      router.push(
        `/chat/${sessionId}`,
      );

      return;
    }

    const selectedSession =
      sessions.find(
        (item) =>
          item.id === sessionId,
      );

    if (!selectedSession) {
      return;
    }

    actionLock.current = true;

    const previousSession =
      session;

    const previousMessages =
      messages;

    setSessionLoading(true);
    setError("");

    setSelectedArtifact(null);
    setArtifactOpen(false);

    setHasStreamingResponse(
      false,
    );

    setInput("");

    setEditingMessageId(null);
    setEditValue("");

    setSidebarOpen(false);

    setSession(
      selectedSession,
    );

    setMessages([]);

    /*
     * Update URL immediately.
     */
    router.push(
      `/chat/${sessionId}`,
    );

    try {
      const sessionMessages =
        await getMessages(
          sessionId,
        );

      setMessages(
        sessionMessages,
      );

      /*
       * Recover title locally if the backend
       * still reports "New chat".
       */
      const firstUserMessage =
        sessionMessages.find(
          (message) =>
            message.role ===
            "user",
        );

      if (
        firstUserMessage &&
        (
          !selectedSession.title ||
          selectedSession.title
            .trim()
            .toLowerCase() ===
            "new chat"
        )
      ) {
        const generatedTitle =
          createConversationTitle(
            firstUserMessage.content,
          );

        setSession(
          (current) =>
            current
              ? {
                  ...current,
                  title:
                    generatedTitle,
                }
              : current,
        );

        setSessions(
          (current) =>
            current.map(
              (item) =>
                item.id ===
                selectedSession.id
                  ? {
                      ...item,
                      title:
                        generatedTitle,
                    }
                  : item,
            ),
        );
      }
    } catch {
      setSession(
        previousSession,
      );

      setMessages(
        previousMessages,
      );

      setError(
        "Unable to load that conversation.",
      );
    } finally {
      setSessionLoading(
        false,
      );

      actionLock.current =
        false;
    }
  }

  /*
   * Create a new conversation.
   */
  async function handleCreateSession() {
    if (
      interactionBusy ||
      actionLock.current
    ) {
      return;
    }

    actionLock.current = true;

    setSessionLoading(true);
    setError("");

    setSelectedArtifact(null);
    setArtifactOpen(false);

    setHasStreamingResponse(
      false,
    );

    setInput("");

    setEditingMessageId(null);
    setEditValue("");

    setSidebarOpen(false);

    try {
      const newSession =
        await createSession(
          "New chat",
        );

      setSessions(
        (current) => [
          newSession,
          ...current.filter(
            (item) =>
              item.id !==
              newSession.id,
          ),
        ],
      );

      setSession(
        newSession,
      );

      setMessages([]);

      /*
       * Give every new conversation
       * its own dynamic URL.
       */
      router.push(
        `/chat/${newSession.id}`,
      );
    } catch {
      setError(
        "Unable to create a new conversation.",
      );
    } finally {
      setSessionLoading(
        false,
      );

      actionLock.current =
        false;
    }
  }

  /*
   * Open artifact.
   */
  const handleOpenArtifact =
    useCallback(
      (message: Message) => {
        if (
          !message.artifact ||
          streaming ||
          sessionLoading
        ) {
          return;
        }

        setSelectedArtifact(
          message.artifact,
        );

        setArtifactOpen(true);
      },
      [
        streaming,
        sessionLoading,
      ],
    );

  /*
   * Close artifact viewer.
   */
  const handleCloseArtifact =
    useCallback(() => {
      setArtifactOpen(false);
      setSelectedArtifact(
        null,
      );
    }, []);

  /*
   * Start editing a user message.
   */
  const handleEditStart =
    useCallback(
      (message: Message) => {
        if (
          interactionBusy ||
          actionLock.current
        ) {
          return;
        }

        if (
          message.role !== "user"
        ) {
          return;
        }

        setError("");

        setEditingMessageId(
          message.id,
        );

        setEditValue(
          message.content,
        );
      },
      [interactionBusy],
    );

  /*
   * Cancel editing.
   */
  const handleEditCancel =
    useCallback(() => {
      if (streaming) {
        return;
      }

      setEditingMessageId(
        null,
      );

      setEditValue("");
    }, [streaming]);

  /*
   * Save edited message.
   */
  const handleEditSave =
    useCallback(async () => {
      if (
        !editingMessageId ||
        !editValue.trim() ||
        interactionBusy ||
        actionLock.current ||
        !session
      ) {
        return;
      }

      const messageId =
        editingMessageId;

      const content =
        editValue.trim();

      actionLock.current = true;

      setError("");

      setSelectedArtifact(
        null,
      );

      setArtifactOpen(false);

      setHasStreamingResponse(
        false,
      );

      setEditingMessageId(
        null,
      );

      setEditValue("");

      try {
        const assistantMessage =
          await editMessage(
            session.id,
            messageId,
            content,
            provider,
          );

        const updatedMessages =
          await getMessages(
            session.id,
          );

        setMessages(
          updatedMessages,
        );

        const editedIndex =
          updatedMessages.findIndex(
            (message) =>
              message.id ===
              messageId,
          );

        /*
         * If the first user message was edited,
         * update the sidebar title.
         */
        if (
          editedIndex === 0
        ) {
          const generatedTitle =
            createConversationTitle(
              content,
            );

          setSession(
            (current) =>
              current
                ? {
                    ...current,
                    title:
                      generatedTitle,
                  }
                : current,
          );

          setSessions(
            (current) =>
              current.map(
                (item) =>
                  item.id ===
                  session.id
                    ? {
                        ...item,
                        title:
                          generatedTitle,
                      }
                    : item,
              ),
          );
        }

        if (
          !assistantMessage ||
          assistantMessage.role !==
            "assistant"
        ) {
          throw new Error(
            "The assistant did not return a valid response.",
          );
        }
      } catch (
        operationError
      ) {
        setError(
          operationError instanceof
            Error
            ? operationError.message
            : "Unable to edit message.",
        );

        try {
          const restoredMessages =
            await getMessages(
              session.id,
            );

          setMessages(
            restoredMessages,
          );
        } catch {
          // Keep current UI.
        }
      } finally {
        actionLock.current =
          false;
      }
    }, [
      editingMessageId,
      editValue,
      interactionBusy,
      session,
      provider,
    ]);

  /*
   * Retry assistant response.
   */
  const handleRetry =
    useCallback(
      async (
        message: Message,
      ) => {
        if (
          interactionBusy ||
          actionLock.current ||
          message.role !==
            "assistant" ||
          !session
        ) {
          return;
        }

        actionLock.current =
          true;

        setError("");

        setSelectedArtifact(
          null,
        );

        setArtifactOpen(false);

        setHasStreamingResponse(
          false,
        );

        setEditingMessageId(
          null,
        );

        setEditValue("");

        try {
          const assistantMessage =
            await retryMessage(
              session.id,
              message.id,
              provider,
            );

          const updatedMessages =
            await getMessages(
              session.id,
            );

          setMessages(
            updatedMessages,
          );

          if (
            !assistantMessage ||
            assistantMessage.role !==
              "assistant"
          ) {
            throw new Error(
              "The assistant did not return a valid response.",
            );
          }
        } catch (
          operationError
        ) {
          setError(
            operationError instanceof
              Error
              ? operationError.message
              : "Unable to retry message.",
          );

          try {
            const restoredMessages =
              await getMessages(
                session.id,
              );

            setMessages(
              restoredMessages,
            );
          } catch {
            // Keep current UI.
          }
        } finally {
          actionLock.current =
            false;
        }
      },
      [
        interactionBusy,
        session,
        provider,
      ],
    );

  /*
   * Submit a new user message.
   */
  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (
      actionLock.current ||
      streaming ||
      sessionLoading
    ) {
      return;
    }

    if (!session) {
      setError(
        "Select a conversation first.",
      );

      return;
    }

    const content =
      input.trim();

    if (!content) {
      return;
    }

    actionLock.current = true;

    setError("");

    setInput("");

    setSelectedArtifact(
      null,
    );

    setArtifactOpen(false);

    setHasStreamingResponse(
      false,
    );

    const isFirstMessage =
      messages.length === 0;

    /*
     * Generate title for the first message.
     */
    if (isFirstMessage) {
      const generatedTitle =
        createConversationTitle(
          content,
        );

      setSession(
        (current) =>
          current
            ? {
                ...current,
                title:
                  generatedTitle,
              }
            : current,
      );

      setSessions(
        (current) =>
          current.map(
            (item) =>
              item.id ===
              session.id
                ? {
                    ...item,
                    title:
                      generatedTitle,
                  }
                : item,
          ),
      );
    }

    const userMessage: Message =
      {
        id: crypto.randomUUID(),
        session_id:
          session.id,
        role: "user",
        content,
        provider: null,
        model: null,
        sources: [],
        created_at:
          new Date().toISOString(),
        artifact: null,
      };

    setMessages(
      (current) => [
        ...current,
        userMessage,
      ],
    );

    try {
      /*
       * useChatStream already has the
       * current session and provider.
       */
      await sendMessage(
        content,
      );
    } finally {
      actionLock.current =
        false;
    }
  }

  const displayError =
    error || streamError;

  if (initializing) {
    return (
      <main className="flex h-screen items-center justify-center bg-neutral-950 text-white">
        <div className="flex items-center gap-2 text-sm text-neutral-500">
          <span className="h-2 w-2 animate-pulse rounded-full bg-neutral-500" />
          Starting...
        </div>
      </main>
    );
  }

  return (
    <main className="h-screen overflow-hidden bg-neutral-950 text-white">
      <div className="flex h-full">
        {/* Desktop sidebar */}
        <aside
          className={`hidden h-full shrink-0 border-r border-neutral-800 bg-neutral-950 transition-[width] duration-200 lg:block ${
            sidebarCollapsed
              ? "w-14"
              : "w-[260px]"
          }`}
        >
          <Sidebar
            sessions={sessions}
            currentSessionId={
              session?.id ?? null
            }
            loading={
              interactionBusy
            }
            collapsed={
              sidebarCollapsed
            }
            onSelect={
              handleSessionSelect
            }
            onCreate={
              handleCreateSession
            }
          />
        </aside>

        {/* Mobile sidebar */}
        {sidebarOpen && (
          <div className="fixed inset-0 z-50 lg:hidden">
            <button
              type="button"
              aria-label="Close navigation"
              className="absolute inset-0 bg-black/70"
              onClick={() =>
                setSidebarOpen(
                  false,
                )
              }
            />

            <aside className="relative h-full w-[280px] max-w-[85vw] border-r border-neutral-800 bg-neutral-950 shadow-2xl">
              <Sidebar
                sessions={sessions}
                currentSessionId={
                  session?.id ?? null
                }
                loading={
                  interactionBusy
                }
                mobile
                onSelect={
                  handleSessionSelect
                }
                onCreate={
                  handleCreateSession
                }
                onClose={() =>
                  setSidebarOpen(
                    false,
                  )
                }
              />
            </aside>
          </div>
        )}

        {/* Main application */}
        <section className="min-w-0 flex-1">
          <div className="flex h-full min-w-0">
            {/* Chat */}
            <div className="min-w-0 flex-1">
              <ChatPane
                session={session}
                messages={messages}
                providers={
                  providers
                }
                provider={
                  provider
                }
                input={input}
                loading={
                  streaming
                }
                error={
                  displayError
                }
                sessionLoading={
                  sessionLoading
                }
                hasStreamingResponse={
                  hasStreamingResponse
                }
                editingMessageId={
                  editingMessageId
                }
                editValue={
                  editValue
                }
                onEditStart={
                  handleEditStart
                }
                onEditChange={
                  setEditValue
                }
                onEditCancel={
                  handleEditCancel
                }
                onEditSave={
                  handleEditSave
                }
                onRetry={
                  handleRetry
                }
                artifactOpen={
                  artifactOpen
                }
                onOpenArtifact={
                  handleOpenArtifact
                }
                onProviderChange={
                  setProvider
                }
                onInputChange={
                  setInput
                }
                onSubmit={
                  handleSubmit
                }
                onOpenSidebar={() => {
                  if (
                    typeof window !==
                      "undefined" &&
                    window.innerWidth <
                      1024
                  ) {
                    setSidebarOpen(
                      true,
                    );
                  } else {
                    setSidebarCollapsed(
                      (current) =>
                        !current,
                    );
                  }
                }}
              />
            </div>

            {/* Desktop artifact viewer */}
            {artifactOpen &&
              selectedArtifact && (
                <aside className="hidden h-full w-[440px] shrink-0 border-l border-neutral-800 bg-neutral-950 lg:block">
                  <ArtifactViewer
                    artifact={
                      selectedArtifact
                    }
                    onClose={
                      handleCloseArtifact
                    }
                  />
                </aside>
              )}
          </div>
        </section>
      </div>

      {/* Mobile artifact drawer */}
      {artifactOpen &&
        selectedArtifact && (
          <div className="fixed inset-0 z-50 lg:hidden">
            <button
              type="button"
              aria-label="Close artifact viewer"
              className="absolute inset-0 bg-black/70"
              onClick={
                handleCloseArtifact
              }
            />

            <div className="absolute inset-x-0 bottom-0 top-8 overflow-hidden rounded-t-2xl border border-neutral-800 bg-neutral-950 shadow-2xl">
              <ArtifactViewer
                artifact={
                  selectedArtifact
                }
                onClose={
                  handleCloseArtifact
                }
              />
            </div>
          </div>
        )}
    </main>
  );
}