"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { BarChartCard } from "@/components/BarChartCard";
import { ChatMessageBody } from "@/components/ChatMessageBody";
import { InsightLineChart } from "@/components/InsightLineChart";
import { DemoDataPanel } from "@/components/DemoDataPanel";
import { AdminUserPanel } from "@/components/AdminUserPanel";
import { chat, ChatResponse, clearToken, getToken, isTokenFresh, tokenHasScope, ToolTrace } from "@/lib/backend";

type Msg = { id: number; role: "user" | "assistant"; content: string };

function CitationsCard({
  citations,
}: {
  citations: NonNullable<ChatResponse["citations"]>;
}) {
  if (!citations?.length) return null;
  return (
    <div className="mt-4 rounded-xl bg-zinc-950/50 p-3 ring-1 ring-white/10">
      <div className="text-xs font-medium text-zinc-200">Document citations</div>
      <ul className="mt-2 space-y-2 text-xs text-zinc-400">
        {citations.map((c) => (
          <li key={c.chunk_id} className="rounded-lg bg-zinc-900/60 p-2 ring-1 ring-white/5">
            <span className="text-zinc-300">
              [{c.chunk_id}] {c.source_name} p.{c.page_number ?? "?"} {c.section ? `· ${c.section}` : ""}
            </span>
            <div className="mt-1 text-zinc-500 line-clamp-3">{c.excerpt}</div>
          </li>
        ))}
      </ul>
    </div>
  );
}

function TraceCard({ trace }: { trace: ToolTrace[] }) {
  return (
    <div className="rounded-2xl bg-zinc-900 p-4 ring-1 ring-white/10">
      <div className="text-sm font-medium text-zinc-200">Tool trace</div>
      <div className="mt-3 space-y-2">
        {trace.map((t, idx) => (
          <div key={`${t.name}-${idx}`} className="rounded-xl bg-zinc-950/50 p-3 ring-1 ring-white/10">
            <div className="text-xs font-medium text-zinc-200">{t.name}</div>
            <div className="mt-1 text-xs text-zinc-400">{t.output_summary}</div>
          </div>
        ))}
        {!trace.length && <div className="text-sm text-zinc-500">No trace yet.</div>}
      </div>
    </div>
  );
}

export function ChatShell() {
  const [authed, setAuthed] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<Msg[]>([]);
  const [lastResponse, setLastResponse] = useState<ChatResponse | null>(null);
  const scrollAnchorRef = useRef<HTMLDivElement>(null);
  const messageIdRef = useRef(0);

  useEffect(() => {
    try {
      const t = getToken();
      if (t && isTokenFresh(t)) {
        setAuthed(true);
        setIsAdmin(tokenHasScope(t, "admin"));
      } else {
        if (t) clearToken();
        setAuthed(false);
        setIsAdmin(false);
      }
    } catch {
      setAuthed(false);
      setIsAdmin(false);
    }
  }, []);

  useEffect(() => {
    scrollAnchorRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loading]);

  const onAsk = useCallback(async () => {
    const q = question.trim();
    if (!q) return;
    setError(null);
    setLoading(true);
    setMessages((m) => [...m, { id: ++messageIdRef.current, role: "user", content: q }]);
    setQuestion("");
    try {
      const res = await chat(q);
      setLastResponse(res);
      const answer = typeof res.answer === "string" ? res.answer : "";
      setMessages((m) => [...m, { id: ++messageIdRef.current, role: "assistant", content: answer }]);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Request failed";
      if (msg.includes("(401)")) {
        setAuthed(false);
        setIsAdmin(false);
        setError("Session expired — sign in again from the login page.");
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  }, [question]);

  const sources = useMemo(() => lastResponse?.sources ?? [], [lastResponse]);
  const trace = useMemo(() => lastResponse?.tool_trace ?? [], [lastResponse]);
  const chart = lastResponse?.chart ?? null;
  const citations = useMemo(() => lastResponse?.citations ?? [], [lastResponse]);
  const routeKind = lastResponse?.route_kind;

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <div className="lg:col-span-2 rounded-2xl bg-zinc-900 p-4 ring-1 ring-white/10">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <div className="text-sm font-medium text-zinc-200">Chat</div>
            <div className="mt-1 text-xs text-zinc-400">
              Try: “Which titles performed best in 2025?” or “Which city had the strongest engagement last month?”
            </div>
          </div>
        </div>

        <div className="mt-4 h-[420px] overflow-auto rounded-xl bg-zinc-950/40 p-4 ring-1 ring-white/10">
          <div className="space-y-3">
            {messages.map((m) => (
              <div
                key={m.id}
                className={[
                  "max-w-[92%] rounded-2xl px-4 py-3 text-sm leading-6 ring-1 ring-white/10",
                  m.role === "user"
                    ? "ml-auto bg-indigo-500/15 text-zinc-50"
                    : "mr-auto bg-zinc-900/70 text-zinc-100",
                ].join(" ")}
              >
                <ChatMessageBody role={m.role} content={m.content} />
              </div>
            ))}
            <div ref={scrollAnchorRef} aria-hidden className="h-px w-full shrink-0" />
            {!messages.length && (
              <div className="text-sm text-zinc-500">
                Ingest demo data from the panel, then ask a question.
              </div>
            )}
          </div>
        </div>

        <div className="mt-4 flex gap-2">
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") onAsk();
            }}
            className="flex-1 rounded-xl bg-zinc-950/60 px-4 py-3 text-sm text-zinc-100 ring-1 ring-white/10 outline-none focus:ring-2 focus:ring-indigo-400/40"
            placeholder={authed ? "Ask a business question…" : "Sign in required…"}
            disabled={loading || !authed}
          />
          <button
            onClick={onAsk}
            className="rounded-xl bg-zinc-100 px-4 py-3 text-sm font-medium text-zinc-950 hover:bg-white disabled:opacity-50"
            disabled={loading || !authed}
          >
            {loading ? "Working…" : "Send"}
          </button>
        </div>

        {error && <div className="mt-3 text-sm text-rose-300">{error}</div>}

        <div className="mt-4 flex flex-wrap items-center gap-2 text-xs">
          {routeKind && (
            <span className="rounded-full bg-emerald-500/15 px-3 py-1 text-emerald-200 ring-1 ring-emerald-500/30">
              route: {routeKind}
            </span>
          )}
          {lastResponse?.sql_tables_used?.map((t) => (
            <span key={t} className="rounded-full bg-zinc-800 px-3 py-1 text-zinc-200 ring-1 ring-white/10">
              sql:{t}
            </span>
          ))}
        </div>

        <div className="mt-4 flex flex-wrap gap-2 text-xs">
          {sources.map((s) => (
            <span key={s} className="rounded-full bg-zinc-800 px-3 py-1 text-zinc-200 ring-1 ring-white/10">
              {s}
            </span>
          ))}
        </div>

        <CitationsCard citations={citations} />
      </div>

      <div className="space-y-6">
        <DemoDataPanel disabled={!authed || loading} />
        {isAdmin && <AdminUserPanel disabled={!authed || loading} />}
        {chart?.type === "bar" && Array.isArray(chart.data) ? (
          <BarChartCard title={chart.title} data={chart.data} />
        ) : chart?.type === "line" && Array.isArray(chart.data) ? (
          <InsightLineChart title={chart.title} data={chart.data} />
        ) : (
          <div className="rounded-2xl bg-zinc-900 p-4 ring-1 ring-white/10">
            <div className="text-sm font-medium text-zinc-200">Insights</div>
            <div className="mt-2 text-sm text-zinc-500">Ask a question that triggers an analytics chart.</div>
          </div>
        )}
        <TraceCard trace={trace} />
      </div>
    </div>
  );
}

