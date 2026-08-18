import { Sparkles } from "lucide-react";

import { ApiStatus } from "../components/ApiStatus";

export function FoundationPage() {
  return (
    <section className="space-y-8">
      <div className="max-w-2xl">
        <div className="mb-4 flex items-center gap-2 text-sm font-medium text-primary">
          <Sparkles className="size-4" aria-hidden="true" />
          Development foundation
        </div>
        <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">Agentic AI Academic Planning Platform</h1>
        <p className="mt-4 text-base leading-7 text-muted-foreground">
          The application foundation is ready for the approved, phased implementation of AAIAPP.
        </p>
      </div>
      <ApiStatus />
    </section>
  );
}
