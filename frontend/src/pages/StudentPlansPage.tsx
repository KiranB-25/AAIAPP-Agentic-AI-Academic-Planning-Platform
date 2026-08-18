import { useCallback, useEffect, useState } from "react";
import { BookOpenCheck, CheckCircle2 } from "lucide-react";

import { AppShell } from "../layouts/AppShell";
import { ApiError } from "../services/api-client";
import { listGoals } from "../services/goal-service";
import { downloadPlanPdf, generatePlan, listPlans, updateTaskCompletion } from "../services/plan-service";
import type { AcademicGoal } from "../types/goals";
import type { StudyPlan } from "../types/plans";

export function StudentPlansPage() {
  const [plans, setPlans] = useState<StudyPlan[]>([]);
  const [goals, setGoals] = useState<AcademicGoal[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [loadedPlans, loadedGoals] = await Promise.all([listPlans(), listGoals()]);
      setPlans(loadedPlans);
      setGoals(loadedGoals);
    } catch (caught) {
      setError(caught instanceof ApiError && caught.status !== 500 ? caught.message : "Unable to load your study plans. Please try again.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  async function create(goal: AcademicGoal) {
    setBusyId(goal.id);
    setError(null);
    try {
      const plan = await generatePlan(goal.id);
      setPlans((current) => [plan, ...current.filter((item) => item.id !== plan.id)]);
      setGoals((current) => current.map((item) => item.id === goal.id ? { ...item, status: "plan_generated", is_editable: false } : item));
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Unable to generate the study plan. Please try again.");
    } finally { setBusyId(null); }
  }

  async function toggle(plan: StudyPlan, taskId: number, complete: boolean) {
    setBusyId(taskId);
    setError(null);
    try {
      const updated = await updateTaskCompletion(taskId, complete);
      setPlans((current) => current.map((item) => {
        if (item.id !== plan.id) return item;
        const tasks = item.tasks.map((task) => task.id === taskId ? updated.task : task);
        return { ...item, tasks, progress: updated.progress };
      }));
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Unable to update this task. Please try again.");
    } finally { setBusyId(null); }
  }

  async function exportPlan(planId: number) {
    setBusyId(planId);
    setError(null);
    try {
      await downloadPlanPdf(planId);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to export the study plan. Please try again.");
    } finally { setBusyId(null); }
  }

  const pendingGoals = goals.filter((goal) => goal.status === "pending");

  return <AppShell><div className="mx-auto max-w-5xl space-y-8">
    <header><p className="text-sm font-medium text-primary">Student workspace</p><h1 className="mt-2 text-3xl font-semibold">Study plans</h1><p className="mt-2 text-sm text-muted-foreground">Follow your ordered academic tasks and track completion.</p></header>
    {error && <div className="flex items-center justify-between gap-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3" role="alert"><span className="text-sm text-destructive">{error}</span><button className="text-sm font-semibold" onClick={() => void load()}>Retry</button></div>}
    {isLoading ? <div className="rounded-xl border bg-card p-8 text-center text-sm text-muted-foreground" role="status">Loading study plans…</div> : <>
      {pendingGoals.length > 0 && <section className="rounded-xl border bg-card p-5"><h2 className="font-semibold">Goals ready for planning</h2><div className="mt-4 flex flex-wrap gap-3">{pendingGoals.map((goal) => <button key={goal.id} disabled={busyId !== null} className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground disabled:opacity-60" onClick={() => void create(goal)}>{busyId === goal.id ? "Generating plan…" : `Generate plan for ${goal.subject}`}</button>)}</div></section>}
      {plans.length === 0 ? <section className="rounded-xl border border-dashed bg-card p-10 text-center"><BookOpenCheck className="mx-auto size-9 text-muted-foreground"/><h2 className="mt-4 text-lg font-semibold">No study plan yet</h2><p className="mt-2 text-sm text-muted-foreground">Create an academic goal, then generate its structured study plan here.</p></section>
      : plans.map((plan) => <PlanCard key={plan.id} plan={plan} goal={goals.find((goal) => goal.id === plan.goal_id)} busyId={busyId} onToggle={toggle} onExport={exportPlan} />)}
    </>}
  </div></AppShell>;
}

function PlanCard({ plan, goal, busyId, onToggle, onExport }: { plan: StudyPlan; goal?: AcademicGoal; busyId: number | null; onToggle: (plan: StudyPlan, taskId: number, complete: boolean) => Promise<void>; onExport: (planId: number) => Promise<void> }) {
  return <article className="rounded-xl border bg-card p-5 shadow-sm sm:p-7">
    <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between"><div><span className="text-xs font-semibold uppercase text-primary">{plan.status}</span><h2 className="mt-2 text-2xl font-semibold">{goal?.subject ?? "Study plan"}</h2><p className="mt-2 text-sm leading-6 text-muted-foreground">{plan.summary}</p><button className="mt-3 rounded border px-3 py-2 text-sm font-semibold" disabled={busyId !== null} onClick={() => void onExport(plan.id)}>Download PDF</button></div><div className="min-w-36" aria-label={`Progress ${plan.progress}%`}><div className="flex justify-between text-sm"><span>Progress</span><strong>{plan.progress}%</strong></div><div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-200"><div className="h-full bg-primary" style={{ width: `${plan.progress}%` }} /></div></div></div>
  <ol className="mt-7 space-y-4">{plan.tasks.map((task) => <li key={task.id} className="rounded-lg border p-4"><div className="flex items-start gap-3"><input id={`task-${task.id}`} type="checkbox" checked={task.is_completed} disabled={busyId !== null} aria-label={`Mark ${task.title} complete`} onChange={(event) => void onToggle(plan, task.id, event.target.checked)} className="mt-1 size-4"/><div><p className="text-xs font-semibold uppercase text-muted-foreground">Week {task.week}</p><label htmlFor={`task-${task.id}`} className="mt-1 block font-semibold">{task.title}</label><p className="mt-2 text-sm leading-6 text-muted-foreground">{task.description}</p><p className="mt-2 text-sm"><strong>Learning objective:</strong> {task.objective}</p><p className="mt-2 text-sm"><strong>Method:</strong> {task.method}</p>{task.revision_checkpoint && <p className="mt-2 text-sm"><strong>Revision checkpoint</strong></p>}{task.is_completed && <p className="mt-2 flex items-center gap-1 text-xs text-success" role="status"><CheckCircle2 className="size-3"/> Completed</p>}</div></div></li>)}</ol>
  </article>;
}
