import { useEffect, useState } from "react";
import { BookOpen, CalendarDays, Plus, Target } from "lucide-react";

import { GoalForm } from "../components/goals/GoalForm";
import { AppShell } from "../layouts/AppShell";
import { ApiError } from "../services/api-client";
import { createGoal, listGoals, updateGoal } from "../services/goal-service";
import type { AcademicGoal, GoalCreateRequest } from "../types/goals";

type ViewMode = "list" | "create" | "detail" | "edit";

export function StudentGoalsPage() {
  const [goals, setGoals] = useState<AcademicGoal[]>([]);
  const [selectedGoal, setSelectedGoal] = useState<AcademicGoal | null>(null);
  const [mode, setMode] = useState<ViewMode>("list");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string[]> | undefined>();
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    listGoals()
      .then(setGoals)
      .catch((caught) => setError(caught instanceof ApiError ? caught.message : "Unable to load academic goals."))
      .finally(() => setIsLoading(false));
  }, []);

  function openGoal(goal: AcademicGoal) {
    setSelectedGoal(goal);
    setMode("detail");
    setError(null);
    setSuccess(null);
  }

  async function saveGoal(values: GoalCreateRequest) {
    setIsSaving(true);
    setError(null);
    setFieldErrors(undefined);
    try {
      if (mode === "edit" && selectedGoal) {
        const updated = await updateGoal(selectedGoal.id, values);
        setGoals((current) => current.map((goal) => goal.id === updated.id ? updated : goal));
        setSelectedGoal(updated);
        setMode("detail");
        setSuccess("Academic goal updated successfully.");
      } else {
        const created = await createGoal(values);
        setGoals((current) => [created, ...current]);
        setSelectedGoal(created);
        setMode("detail");
        setSuccess("Academic goal created successfully.");
      }
    } catch (caught) {
      if (caught instanceof ApiError) {
        setError(caught.message);
        setFieldErrors(caught.fieldErrors);
      } else setError("Unable to save the academic goal.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-5xl space-y-8">
        <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm font-medium text-primary">Student workspace</p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight">Academic goals</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">Define focused academic objectives before creating a structured study plan in a later step.</p>
          </div>
          {mode !== "create" && <button className="inline-flex items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground" onClick={() => { setMode("create"); setError(null); setSuccess(null); }}><Plus className="size-4" /> New goal</button>}
        </header>

        {success && <p className="rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800" role="status">{success}</p>}
        {error && <p className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-destructive" role="alert">{error}</p>}

        {(mode === "create" || mode === "edit") && (
          <section className="rounded-xl border border-border bg-card p-5 shadow-sm sm:p-7" aria-labelledby="goal-form-title">
            <h2 id="goal-form-title" className="text-xl font-semibold">{mode === "edit" ? "Edit academic goal" : "Create academic goal"}</h2>
            <p className="mb-6 mt-1 text-sm text-muted-foreground">All fields except study intensity are required.</p>
            <GoalForm goal={mode === "edit" ? selectedGoal ?? undefined : undefined} isSubmitting={isSaving} serverErrors={fieldErrors} onSubmit={saveGoal} onCancel={() => setMode(selectedGoal ? "detail" : "list")} />
          </section>
        )}

        {mode === "detail" && selectedGoal && (
          <section className="rounded-xl border border-border bg-card p-5 shadow-sm sm:p-7">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <span className="inline-flex rounded-full bg-amber-50 px-2.5 py-1 text-xs font-semibold capitalize text-amber-800">{selectedGoal.status}</span>
                <h2 className="mt-3 text-2xl font-semibold">{selectedGoal.subject}</h2>
              </div>
              <div className="flex gap-3">
                <button className="rounded-lg border border-border px-4 py-2 text-sm font-medium" onClick={() => setMode("list")}>Back to goals</button>
                {selectedGoal.is_editable && <button className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground" onClick={() => { setMode("edit"); setError(null); setSuccess(null); }}>Edit goal</button>}
              </div>
            </div>
            <div className="mt-7 grid gap-5 border-y border-border py-5 sm:grid-cols-3">
              <Info icon={<CalendarDays className="size-4" />} label="Duration" value={`${selectedGoal.duration} weeks`} />
              <Info icon={<Target className="size-4" />} label="Intensity" value={selectedGoal.intensity || "Not specified"} />
              <Info icon={<BookOpen className="size-4" />} label="Created" value={new Date(selectedGoal.created_at).toLocaleDateString()} />
            </div>
            <div className="mt-6"><h3 className="text-sm font-semibold">Objective or description</h3><p className="mt-2 whitespace-pre-wrap text-sm leading-7 text-muted-foreground">{selectedGoal.description}</p></div>
            {selectedGoal.status === "pending" && <p className="mt-6 rounded-lg bg-muted px-4 py-3 text-sm text-muted-foreground">This goal is pending and ready for the future planning step.</p>}
          </section>
        )}

        {mode === "list" && (
          <section aria-label="Academic goal list">
            {isLoading ? <div className="rounded-xl border border-border bg-card p-8 text-center text-sm text-muted-foreground" role="status">Loading academic goals…</div>
              : goals.length === 0 ? <div className="rounded-xl border border-dashed border-border bg-card p-10 text-center"><Target className="mx-auto size-8 text-muted-foreground" /><h2 className="mt-4 text-lg font-semibold">No academic goals yet</h2><p className="mx-auto mt-2 max-w-md text-sm text-muted-foreground">Create your first goal to define what you want to study and how long you plan to spend.</p></div>
              : <div className="grid gap-4 md:grid-cols-2">{goals.map((goal) => <article key={goal.id} className="rounded-xl border border-border bg-card p-5 shadow-sm"><div className="flex items-start justify-between gap-3"><h2 className="font-semibold">{goal.subject}</h2><span className="rounded-full bg-amber-50 px-2.5 py-1 text-xs font-semibold capitalize text-amber-800">{goal.status}</span></div><p className="mt-3 line-clamp-3 text-sm leading-6 text-muted-foreground">{goal.description}</p><div className="mt-5 flex items-center justify-between border-t border-border pt-4"><span className="text-sm text-muted-foreground">{goal.duration} weeks</span><button className="text-sm font-semibold text-primary" onClick={() => openGoal(goal)}>View details</button></div></article>)}</div>}
          </section>
        )}
      </div>
    </AppShell>
  );
}

function Info({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return <div><p className="flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">{icon}{label}</p><p className="mt-2 text-sm font-medium">{value}</p></div>;
}
