"use client";

import { useMemo } from "react";
import DOMPurify from "dompurify";

interface SandboxedIframeProps {
  content: string;
  title: string;
}

export function SandboxedIframe({
  content,
  title,
}: SandboxedIframeProps) {
  const cleanHtml = useMemo(() => {
    if (typeof window === "undefined") {
      return content;
    }

    return DOMPurify.sanitize(content, {
      WHOLE_DOCUMENT: true,
      ADD_TAGS: ["style"],
      FORBID_TAGS: [
        "script",
        "object",
        "embed",
        "base",
        "meta",
      ],
      FORBID_ATTR: [
        "onerror",
        "onload",
        "onclick",
        "onmouseover",
        "onfocus",
        "onblur",
      ],
    });
  }, [content]);

  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden rounded-xl border border-neutral-800 bg-white">
      <div className="flex shrink-0 items-center justify-between border-b border-neutral-200 bg-neutral-50 px-4 py-3">
        <div className="min-w-0">
          <div className="truncate text-xs font-semibold uppercase tracking-wide text-neutral-700">
            {title}
          </div>

          <div className="mt-0.5 text-[10px] text-neutral-500">
            HTML preview
          </div>
        </div>

        <span className="ml-3 shrink-0 rounded-md border border-neutral-200 bg-white px-2 py-1 text-[10px] font-medium text-neutral-600">
          Sandboxed
        </span>
      </div>

      <div className="min-h-0 flex-1">
        <iframe
          title={title}
          srcDoc={cleanHtml}
          sandbox="allow-scripts"
          referrerPolicy="no-referrer"
          className="h-full min-h-[400px] w-full border-0"
        />
      </div>
    </div>
  );
}