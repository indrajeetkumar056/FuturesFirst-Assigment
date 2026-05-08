import { AppGate } from "@/components/AppGate";
import { ChatShell } from "@/components/ChatShell";

export default function Home() {
  return (
    <main className="min-h-dvh bg-zinc-950 text-zinc-50">
      <AppGate>
        <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-4 py-8">
          <ChatShell />
        </div>
      </AppGate>
    </main>
  );
}
