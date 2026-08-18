import { get, post } from "./api-client";
import type { StudyPlan } from "../types/plans";

export interface PlanReview { id: number; study_plan_id: number; feedback_text: string; decision: "pending" | "approved" | "revision_required"; created_at: string; updated_at: string; }
export function listSupervisorPlans() { return get<StudyPlan[]>("/api/reviews/supervisor/plans/", { authenticated: true }); }
export function submitReview(planId: number, feedback_text: string, decision: PlanReview["decision"]) { return post<PlanReview>(`/api/reviews/supervisor/plans/${planId}/review/`, { feedback_text, decision }, { authenticated: true }); }
export function listStudentReviews() { return get<PlanReview[]>("/api/reviews/student/reviews/", { authenticated: true }); }
