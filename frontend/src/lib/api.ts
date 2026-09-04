const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type Provider = "ollama" | "anthropic";

export interface SourceCitation {
  episode_title: string;
  guest_name: string | null;
  timestamp: string | null;
  url: string | null;
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
    throw new Error("Failed to create session");
  }

  return response.json();
}

export async function getMessages(
  sessionId: string,
): Promise<Message[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/sessions/${sessionId}/messages`,
  );

  if (!response.ok) {
    throw new Error("Failed to load messages");
  }

  return response.json();
}

export async function sendMessage(
  sessionId: string,
  content: string,
  provider?: Provider,
): Promise<Message> {
  const response = await fetch(
    `${API_BASE_URL}/api/sessions/${sessionId}/messages`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        content,
        provider,
      }),
    },
  );

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null);

    throw new Error(
      errorBody?.message ?? "Failed to send message",
    );
  }

  return response.json();
}

export async function getProviders(): Promise<ProvidersResponse> {
  const response = await fetch(`${API_BASE_URL}/api/providers`);

  if (!response.ok) {
    throw new Error("Failed to load providers");
  }

  return response.json();
}