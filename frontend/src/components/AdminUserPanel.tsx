"use client";

import { useState } from "react";

import { createUser } from "@/lib/backend";

type Props = {
  disabled?: boolean;
};

export function AdminUserPanel({ disabled }: Props) {
  const [email, setEmail] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [created, setCreated] = useState<{ email: string; temporary_password: string } | null>(null);

  async function onCreate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setCreated(null);
    setBusy(true);
    try {
      const res = await createUser({
        email: email.trim(),
        first_name: firstName.trim(),
        last_name: lastName.trim(),
      });
      setCreated({ email: res.email, temporary_password: res.temporary_password });
      setEmail("");
      setFirstName("");
      setLastName("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create user");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-2xl bg-zinc-900 p-4 ring-1 ring-white/10">
      <div className="text-sm font-medium text-zinc-200">Add user (admin)</div>
      <p className="mt-1 text-xs text-zinc-400">
        Creates a member with email, first name, and last name. A one-time temporary password is shown here—share it securely with the new user.
      </p>
      <form onSubmit={onCreate} className="mt-3 space-y-2">
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          disabled={disabled || busy}
          className="w-full rounded-lg bg-zinc-950/60 px-3 py-2 text-sm text-zinc-100 ring-1 ring-white/10 outline-none focus:ring-2 focus:ring-indigo-400/40 disabled:opacity-50"
          required
        />
        <div className="grid grid-cols-2 gap-2">
          <input
            placeholder="First name"
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
            disabled={disabled || busy}
            className="rounded-lg bg-zinc-950/60 px-3 py-2 text-sm text-zinc-100 ring-1 ring-white/10 outline-none focus:ring-2 focus:ring-indigo-400/40 disabled:opacity-50"
            required
          />
          <input
            placeholder="Last name"
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            disabled={disabled || busy}
            className="rounded-lg bg-zinc-950/60 px-3 py-2 text-sm text-zinc-100 ring-1 ring-white/10 outline-none focus:ring-2 focus:ring-indigo-400/40 disabled:opacity-50"
            required
          />
        </div>
        <button
          type="submit"
          disabled={disabled || busy}
          className="w-full rounded-lg bg-indigo-500/90 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
        >
          {busy ? "Creating…" : "Create user"}
        </button>
      </form>
      {error && <div className="mt-2 text-xs text-rose-300">{error}</div>}
      {created && (
        <div className="mt-3 rounded-lg bg-emerald-500/10 p-2 text-xs text-emerald-200 ring-1 ring-emerald-500/25">
          <div>
            User <strong className="text-emerald-100">{created.email}</strong> created.
          </div>
          <div className="mt-1 font-mono text-[11px] text-emerald-100/90">Temporary password: {created.temporary_password}</div>
        </div>
      )}
    </div>
  );
}
