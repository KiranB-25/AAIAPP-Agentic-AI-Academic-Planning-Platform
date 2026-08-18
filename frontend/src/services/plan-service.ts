import { download, get, patch, post } from "./api-client";
import type { PlanTaskCompletionUpdate, StudyPlan } from "../types/plans";

const plansPath = "/api/plans/";

export function listPlans(): Promise<StudyPlan[]> {
  return get<StudyPlan[]>(plansPath, { authenticated: true });
}

export function generatePlan(goalId: number): Promise<StudyPlan> {
  return post<StudyPlan>(`${plansPath}goals/${goalId}/generate/`, { request_id: crypto.randomUUID() }, { authenticated: true });
}

export function updateTaskCompletion(taskId: number, isCompleted: boolean): Promise<PlanTaskCompletionUpdate> {
  return patch<PlanTaskCompletionUpdate>(`${plansPath}tasks/${taskId}/`, { is_completed: isCompleted }, { authenticated: true });
}

export async function downloadPlanPdf(planId: number): Promise<void> {
  const url = URL.createObjectURL(await download(`/api/exports/plans/${planId}/`, { authenticated: true }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `study-plan-${planId}.pdf`;
  anchor.click();
  URL.revokeObjectURL(url);
}
