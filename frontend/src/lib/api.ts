const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type Provider = "ollama" | "anthropic";

export interface SourceCitation {
  episode_title: string;
  guest_name: string | null;
  timestamp: string | null;
  url: string | null;
}

export interface MessageArtifact {
  type: "markdown" | "html";
  title: string;
  content: string;
}

export interface Message {
  id: string;
  session_id: string;
  role: string;
  content: string;
  provider: string | null;
  model: string | null;
  sources: SourceCitation[];
  created_at: string;
  artifact?: MessageArtifact | null;
}

export interface Session {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProviderInfo {
  id: Provider;
  name: string;
  model: string;
  configured: boolean;
  available: boolean;
}

export interface ProvidersResponse {
  default_provider: Provider;
  providers: ProviderInfo[];
}

async function parseError(
  response: Response,
  fallback: string,
): Promise<Error> {
  try {
    const body = await response.json().catch(() => null);

    const message =
      body?.message ?? body?.detail?.message ?? body?.detail ?? fallback;

    return new Error(String(message));
  } catch {
    return new Error(fallback);
  }
}

export async function createSession(title?: string): Promise<Session> {
  const response = await fetch(`${API_BASE_URL}/api/sessions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      title: title ?? null,
    }),
  });

  if (!response.ok) {
    throw await parseError(response, "Failed to create session.");
  }

  return response.json();
}

export async function getSessions(): Promise<Session[]> {
  const response = await fetch(`${API_BASE_URL}/api/sessions`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw await parseError(response, "Failed to load sessions.");
  }

  return response.json();
}

export async function getMessages(sessionId: string): Promise<Message[]> {
  if (!sessionId) {
    return [];
  }

  const response = await fetch(
    `${API_BASE_URL}/api/sessions/${encodeURIComponent(sessionId)}/messages`,
    {
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw await parseError(response, "Failed to load messages.");
  }

  return response.json();
}

export async function sendMessage(
  sessionId: string,
  content: string,
  provider?: Provider,
): Promise<Message> {
  if (!sessionId) {
    throw new Error("A conversation is required.");
  }

  const trimmed = content.trim();

  if (!trimmed) {
    throw new Error("Message cannot be empty.");
  }

  const response = await fetch(
    `${API_BASE_URL}/api/sessions/${encodeURIComponent(sessionId)}/messages`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        content: trimmed,
        provider,
      }),
    },
  );

  if (!response.ok) {
    throw await parseError(response, "Failed to send message.");
  }

  return response.json();
}

export async function getProviders(): Promise<ProvidersResponse> {
  const response = await fetch(`${API_BASE_URL}/api/providers`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw await parseError(response, "Failed to load providers.");
  }

  return response.json();
}

export function createConversationTitle(content: string): string {
  const normalized = content.replace(/\s+/g, " ").trim();

  if (!normalized) {
    return "New chat";
  }

  const cleaned = normalized
    .replace(/^(please|can you|could you|would you)\s+/i, "")
    .replace(/[?.!]+$/, "")
    .trim();

  if (!cleaned) {
    return "New chat";
  }

  const words = cleaned.split(/\s+/);

  const title = words.length > 7 ? `${words.slice(0, 7).join(" ")}…` : cleaned;

  return title.charAt(0).toUpperCase() + title.slice(1);
}


export async function editMessage(
  sessionId: string,
  messageId: string,
  content: string,
  provider: Provider | null,
): Promise<Message> {
  const trimmed = content.trim();

  if (!trimmed) {
    throw new Error("Message cannot be empty.");
  }

  const response = await fetch(
    `${API_BASE_URL}/api/sessions/${encodeURIComponent(
      sessionId,
    )}/messages/${encodeURIComponent(messageId)}`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        content: trimmed,
        provider,
      }),
    },
  );

  if (!response.ok) {
    throw await parseError(
      response,
      "Unable to edit message.",
    );
  }

  return response.json();
}


export async function retryMessage(
  sessionId: string,
  messageId: string,
  provider: Provider | null,
): Promise<Message> {
  const response = await fetch(
    `${API_BASE_URL}/api/sessions/${encodeURIComponent(
      sessionId,
    )}/messages/${encodeURIComponent(messageId)}/retry`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        provider,
      }),
    },
  );

  if (!response.ok) {
    throw await parseError(
      response,
      "Unable to retry message.",
    );
  }

  return response.json();
}