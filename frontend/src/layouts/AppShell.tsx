import type { PropsWithChildren } from "react";
import { BrainCircuit } from "lucide-react";

export function AppShell({ children }: PropsWithChildren) {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border bg-card">
        <div className="mx-auto flex h-16 max-w-5xl items-center gap-3 px-5">
          <span className="grid size-9 place-items-center rounded-lg bg-primary text-primary-foreground">
            <BrainCircuit className="size-5" aria-hidden="true" />
          </span>
          <div>
            <p className="text-sm font-semibold tracking-tight">AAIAPP</p>
            <p className="text-xs text-muted-foreground">Academic Planning Platform</p>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-5 py-12">{children}</main>
    </div>
  );
}
