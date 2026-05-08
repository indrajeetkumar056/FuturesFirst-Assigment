"use client";

import ReactMarkdown from "react-markdown";

const assistantMarkdownClass =
  "text-sm leading-relaxed break-words " +
  "[&_p]:mb-3 [&_p:last-child]:mb-0 " +
  "[&_strong]:font-semibold [&_strong]:text-zinc-50 " +
  "[&_em]:italic [&_em]:text-zinc-200 " +
  "[&_ul]:my-2 [&_ul]:list-disc [&_ul]:pl-5 [&_ul]:space-y-1 " +
  "[&_ol]:my-2 [&_ol]:list-decimal [&_ol]:pl-5 [&_ol]:space-y-1 " +
  "[&_li]:pl-0.5 " +
  "[&_h1]:mb-2 [&_h1]:text-base [&_h1]:font-semibold [&_h1]:text-zinc-50 " +
  "[&_h2]:mb-2 [&_h2]:text-sm [&_h2]:font-semibold [&_h2]:text-zinc-100 " +
  "[&_h3]:mb-1 [&_h3]:text-sm [&_h3]:font-medium [&_h3]:text-zinc-100 " +
  "[&_blockquote]:border-l-2 [&_blockquote]:border-zinc-600 [&_blockquote]:pl-3 [&_blockquote]:text-zinc-300 " +
  "[&_code]:rounded [&_code]:bg-zinc-950/80 [&_code]:px-1 [&_code]:py-0.5 [&_code]:text-xs " +
  "[&_pre]:my-2 [&_pre]:overflow-x-auto [&_pre]:rounded-lg [&_pre]:bg-zinc-950/80 [&_pre]:p-3 [&_pre]:text-xs";

type Props = {
  role: "user" | "assistant";
  content: string;
};

export function ChatMessageBody({ role, content }: Props) {
  if (role === "user") {
    return <div className="whitespace-pre-wrap break-words text-sm leading-relaxed">{content}</div>;
  }
  return (
    <div className={assistantMarkdownClass}>
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  );
}
