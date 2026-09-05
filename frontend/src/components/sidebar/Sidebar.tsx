"use client";

import { Session } from "@/lib/api";

interface SidebarProps {
  sessions: Session[];
  currentSessionId: string | null;
  loading?: boolean;
  mobile?: boolean;
  collapsed?: boolean;

  onSelect: (sessionId: string) => void;
  onCreate: () => void;

  onClose?: () => void;
}

function getSessionTitle(session: Session) {
  const title = session.title?.trim();

  if (
    title &&
    title !== "New conversation" &&
    title !== "New chat"
  ) {
    return title;
  }

  return "New chat";
}

function getDateLabel(dateString: string) {
  const date = new Date(dateString);

  if (Number.isNaN(date.getTime())) {
    return "Previous 7 days";
  }

  const now = new Date();

  const startOfToday = new Date(
    now.getFullYear(),
    now.getMonth(),
    now.getDate(),
  );

  const startOfYesterday = new Date(
    startOfToday,
  );

  startOfYesterday.setDate(
    startOfYesterday.getDate() - 1,
  );

  if (date >= startOfToday) {
    return "Today";
  }

  if (date >= startOfYesterday) {
    return "Yesterday";
  }

  return "Previous 7 days";
}

function groupSessions(sessions: Session[]) {
  const groups: Record<string, Session[]> = {};

  for (const session of sessions) {
    const label = getDateLabel(
      session.updated_at,
    );

    if (!groups[label]) {
      groups[label] = [];
    }

    groups[label].push(session);
  }

  return groups;
}

export function Sidebar({
  sessions,
  currentSessionId,
  loading = false,
  mobile = false,
  collapsed = false,
  onSelect,
  onCreate,
  onClose,
}: SidebarProps) {
  if (collapsed && !mobile) {
    return (
      <div className="flex h-full w-14 flex-col items-center border-r border-neutral-800 bg-neutral-950 py-3">
        <div
          className="flex h-8 w-8 items-center justify-center rounded-lg bg-white text-xs font-semibold text-neutral-950"
          aria-label="GrowthGuide"
          title="GrowthGuide"
        >
          G
        </div>

        <button
          type="button"
          onClick={onCreate}
          disabled={loading}
          aria-label="New chat"
          title="New chat"
          className="mt-4 flex h-9 w-9 items-center justify-center rounded-lg border border-neutral-800 text-lg text-neutral-400 transition hover:border-neutral-700 hover:bg-neutral-900 hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
        >
          +
        </button>
      </div>
    );
  }

  const groups = groupSessions(sessions);

  const groupOrder = [
    "Today",
    "Yesterday",
    "Previous 7 days",
  ];

  return (
    <div className="flex h-full min-h-0 flex-col bg-neutral-950">
      {/* Brand */}
      <div className="flex shrink-0 items-center justify-between px-3 py-3">
        <div className="flex min-w-0 items-center gap-2 px-2">
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-white text-xs font-semibold text-neutral-950">
            G
          </div>

          <span className="truncate text-sm font-semibold tracking-tight text-white">
            GrowthGuide
          </span>
        </div>

        {mobile && onClose && (
          <button
            type="button"
            onClick={onClose}
            aria-label="Close sidebar"
            title="Close sidebar"
            className="flex h-8 w-8 items-center justify-center rounded-lg text-neutral-500 transition hover:bg-neutral-900 hover:text-white focus:outline-none focus:ring-2 focus:ring-neutral-700"
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              className="h-4 w-4"
              aria-hidden="true"
            >
              <path
                d="M6 6l12 12M18 6L6 18"
                strokeLinecap="round"
              />
            </svg>
          </button>
        )}
      </div>

      {/* New chat */}
      <div className="px-3 pb-3">
        <button
          type="button"
          onClick={onCreate}
          disabled={loading}
          className="flex w-full items-center gap-2 rounded-lg border border-neutral-800 px-3 py-2.5 text-left text-sm text-neutral-300 transition hover:border-neutral-700 hover:bg-neutral-900 hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
        >
          <span className="text-lg leading-none">
            +
          </span>

          <span>New chat</span>
        </button>
      </div>

      {/* Sessions */}
      <div className="min-h-0 flex-1 overflow-y-auto px-2 pb-4">
        {sessions.length === 0 ? (
          <div className="px-3 py-8 text-center text-xs text-neutral-600">
            No conversations yet.
          </div>
        ) : (
          <div className="space-y-5">
            {groupOrder.map((groupName) => {
              const group = groups[groupName];

              if (!group || group.length === 0) {
                return null;
              }

              return (
                <section key={groupName}>
                  <div className="px-3 pb-2 text-[10px] font-medium uppercase tracking-wider text-neutral-600">
                    {groupName}
                  </div>

                  <div className="space-y-0.5">
                    {group.map((item) => {
                      const active =
                        item.id === currentSessionId;

                      return (
                        <button
                          key={item.id}
                          type="button"
                          disabled={loading}
                          onClick={() =>
                            onSelect(item.id)
                          }
                          title={getSessionTitle(item)}
                          className={`group flex w-full items-center rounded-lg px-3 py-2 text-left text-xs transition ${
                            active
                              ? "bg-neutral-900 text-neutral-100"
                              : "text-neutral-500 hover:bg-neutral-900/70 hover:text-neutral-300"
                          } disabled:cursor-not-allowed disabled:opacity-60`}
                        >
                          <span className="min-w-0 flex-1 truncate">
                            {getSessionTitle(item)}
                          </span>

                          {active && (
                            <span className="ml-2 h-1.5 w-1.5 shrink-0 rounded-full bg-neutral-400" />
                          )}
                        </button>
                      );
                    })}
                  </div>
                </section>
              );
            })}
          </div>
        )}
      </div>

      {/* Knowledge info */}
      <div className="shrink-0 border-t border-neutral-800 px-3 py-3">
        <div className="rounded-lg px-2 py-2">
          <div className="text-[10px] text-neutral-600">
            Transcript knowledge
          </div>

          <div className="mt-1 text-xs leading-5 text-neutral-500">
            Grounded answers from the available podcast
            library.
          </div>
        </div>
      </div>
    </div>
  );
}