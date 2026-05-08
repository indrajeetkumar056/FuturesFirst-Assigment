"use client";

import { type ReactNode, useCallback, useEffect, useState } from "react";

import { clearToken, getToken, isTokenFresh, login } from "@/lib/backend";

type Props = {
  children: ReactNode;
};

export function AppGate({ children }: Props) {
  const [authed, setAuthed] = useState(false);
  const [checked, setChecked] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    try {
      const t = getToken();
      if (t && isTokenFresh(t)) {
        setAuthed(true);
      } else {
        if (t) clearToken();
        setAuthed(false);
      }
    } catch {
      setAuthed(false);
    } finally {
      setChecked(true);
    }
  }, []);

  const onSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      setError(null);
      setSubmitting(true);
      try {
        await login(email.trim(), password);
        setAuthed(true);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Login failed");
      } finally {
        setSubmitting(false);
      }
    },
    [email, password],
  );

  const onLogout = useCallback(() => {
    clearToken();
    setAuthed(false);
    setPassword("");
  }, []);

  if (!checked) {
    return (
      <main className="min-h-dvh bg-zinc-950 text-zinc-50">
        <div className="flex min-h-dvh items-center justify-center text-sm text-zinc-400">Loading…</div>
      </main>
    );
  }

  if (!authed) {
    return (
      <main className="min-h-dvh bg-zinc-950 text-zinc-50">
        <div className="mx-auto flex min-h-dvh w-full max-w-md flex-col justify-center px-4 py-10">
          <div className="mb-8 text-center">
            <h1 className="text-xl font-semibold tracking-tight">Secure AI Insights Assistant</h1>
            <p className="mt-2 text-sm text-zinc-400">Sign in with your account (SQLite-backed).</p>
          </div>
          <form onSubmit={onSubmit} className="rounded-2xl bg-zinc-900 p-6 ring-1 ring-white/10">
            <label className="block text-xs font-medium text-zinc-400">Email</label>
            <input
              type="email"
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full rounded-lg bg-zinc-950/60 px-3 py-2 text-sm text-zinc-100 ring-1 ring-white/10 outline-none focus:ring-2 focus:ring-indigo-400/40"
              required
            />
            <label className="mt-4 block text-xs font-medium text-zinc-400">Password</label>
            <input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full rounded-lg bg-zinc-950/60 px-3 py-2 text-sm text-zinc-100 ring-1 ring-white/10 outline-none focus:ring-2 focus:ring-indigo-400/40"
              required
            />
            {error && <div className="mt-3 text-sm text-rose-300">{error}</div>}
            <button
              type="submit"
              disabled={submitting}
              className="mt-6 w-full rounded-lg bg-indigo-500 py-2.5 text-sm font-medium text-white hover:bg-indigo-400 disabled:opacity-50"
            >
              {submitting ? "Signing in…" : "Sign in"}
            </button>
            <p className="mt-4 text-center text-[11px] text-zinc-500">
              Admin email: <span className="text-zinc-400">adminlocalhost@gmail.com</span> (override with{" "}
              <code className="rounded bg-zinc-800 px-1">ADMIN_EMAIL</code>) / password from{" "}
              <code className="rounded bg-zinc-800 px-1">ADMIN_PASSWORD</code>
            </p>
          </form>
        </div>
      </main>
    );
  }

  return (
    <>
      <header className="flex items-center justify-between gap-4 border-b border-white/10 px-4 py-4 sm:px-6">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Secure AI Insights Assistant</h1>
          <p className="text-sm text-zinc-300">
            Multi-source analytics (SQL + CSV + PDFs) with tool trace and per-request JWT rotation.
          </p>
        </div>
        <div className="flex flex-shrink-0 items-center gap-2">
          <a
            className="rounded-lg bg-zinc-800 px-3 py-2 text-sm text-zinc-100 hover:bg-zinc-700"
            href="http://localhost:8001/docs"
            target="_blank"
            rel="noreferrer"
          >
            Backend API docs
          </a>
          <button
            type="button"
            onClick={onLogout}
            className="rounded-lg border border-white/15 px-3 py-2 text-sm text-zinc-200 hover:bg-white/5"
          >
            Log out
          </button>
        </div>
      </header>
      {children}
    </>
  );
}
