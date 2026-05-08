"use client";

import { useState } from "react";

import { reloadDemoFromDisk } from "@/lib/backend";

type Props = {
  disabled?: boolean;
};

export function DemoDataPanel({ disabled }: Props) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<unknown>(null);

  async function onReload() {
    setError(null);
    setBusy(true);
    try {
      const res = await reloadDemoFromDisk();
      setLastResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Reload failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-2xl bg-zinc-900 p-4 ring-1 ring-white/10">
      <div className="text-sm font-medium text-zinc-200">Demo data</div>
      <p className="mt-1 text-xs text-zinc-400">
        Answers use files under <code className="rounded bg-zinc-800 px-1">backend/demo_data/</code> (CSVs +{" "}
        <code className="rounded bg-zinc-800 px-1">pdfs/</code>). Loaded in memory at server start; no database.
      </p>
      <button
        type="button"
        onClick={onReload}
        disabled={disabled || busy}
        className="mt-3 w-full rounded-lg bg-zinc-100 px-3 py-2 text-sm font-medium text-zinc-950 hover:bg-white disabled:opacity-50"
      >
        {busy ? "Reloading…" : "Reload from disk"}
      </button>
      {error && <div className="mt-2 text-xs text-rose-300">{error}</div>}
      {lastResult != null ? (
        <pre className="mt-2 max-h-40 overflow-auto rounded-lg bg-zinc-950/50 p-2 text-[10px] text-zinc-400">
          {JSON.stringify(lastResult, null, 2)}
        </pre>
      ) : null}
    </div>
  );
}
