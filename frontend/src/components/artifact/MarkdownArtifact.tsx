import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface MarkdownArtifactProps {
  content: string;
}

export function MarkdownArtifact({
  content,
}: MarkdownArtifactProps) {
  return (
    <article className="h-full overflow-y-auto rounded-xl border border-neutral-800 bg-neutral-950">
      <div className="mx-auto max-w-3xl px-6 py-8 sm:px-8 sm:py-10">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            h1: ({ children }) => (
              <h1 className="mb-6 text-2xl font-semibold tracking-tight text-white sm:text-3xl">
                {children}
              </h1>
            ),

            h2: ({ children }) => (
              <h2 className="mb-3 mt-9 border-b border-neutral-800 pb-2 text-lg font-semibold text-white">
                {children}
              </h2>
            ),

            h3: ({ children }) => (
              <h3 className="mb-2 mt-7 text-base font-semibold text-neutral-200">
                {children}
              </h3>
            ),

            p: ({ children }) => (
              <p className="mb-5 text-sm leading-7 text-neutral-300">
                {children}
              </p>
            ),

            ul: ({ children }) => (
              <ul className="mb-5 list-disc space-y-2 pl-6 text-sm leading-6 text-neutral-300">
                {children}
              </ul>
            ),

            ol: ({ children }) => (
              <ol className="mb-5 list-decimal space-y-2 pl-6 text-sm leading-6 text-neutral-300">
                {children}
              </ol>
            ),

            li: ({ children }) => (
              <li className="pl-1">{children}</li>
            ),

            blockquote: ({ children }) => (
              <blockquote className="my-6 border-l-2 border-neutral-600 pl-4 text-sm italic leading-7 text-neutral-400">
                {children}
              </blockquote>
            ),

            strong: ({ children }) => (
              <strong className="font-semibold text-white">
                {children}
              </strong>
            ),

            em: ({ children }) => (
              <em className="text-neutral-200">{children}</em>
            ),

            hr: () => (
              <hr className="my-9 border-neutral-800" />
            ),

            a: ({ href, children }) => (
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-neutral-200 underline decoration-neutral-600 underline-offset-2 transition hover:decoration-neutral-300"
              >
                {children}
              </a>
            ),

            code: ({ className, children }) => {
              const isBlock = Boolean(
                className?.includes("language-"),
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
              <pre className="my-6 overflow-x-auto rounded-xl border border-neutral-800 bg-black p-4 font-mono text-xs leading-6">
                {children}
              </pre>
            ),

            table: ({ children }) => (
              <div className="my-6 overflow-x-auto rounded-xl border border-neutral-800">
                <table className="w-full border-collapse text-left text-xs">
                  {children}
                </table>
              </div>
            ),

            thead: ({ children }) => (
              <thead className="bg-neutral-900 text-neutral-300">
                {children}
              </thead>
            ),

            tbody: ({ children }) => <tbody>{children}</tbody>,

            tr: ({ children }) => <tr>{children}</tr>,

            th: ({ children }) => (
              <th className="border-b border-neutral-800 px-4 py-3 font-semibold">
                {children}
              </th>
            ),

            td: ({ children }) => (
              <td className="border-b border-neutral-800 px-4 py-3 text-neutral-400">
                {children}
              </td>
            ),
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
    </article>
  );
}