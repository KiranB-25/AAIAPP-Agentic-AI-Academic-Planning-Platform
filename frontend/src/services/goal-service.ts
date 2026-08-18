import { get, patch, post } from "./api-client";
import type { AcademicGoal, GoalCreateRequest, GoalUpdateRequest } from "../types/goals";

const goalsPath = "/api/goals/";

export function listGoals(): Promise<AcademicGoal[]> {
  return get<AcademicGoal[]>(goalsPath, { authenticated: true });
}

export function createGoal(goal: GoalCreateRequest): Promise<AcademicGoal> {
  return post<AcademicGoal>(goalsPath, goal, { authenticated: true });
}

export function updateGoal(id: number, goal: GoalUpdateRequest): Promise<AcademicGoal> {
  return patch<AcademicGoal>(`${goalsPath}${id}/`, goal, { authenticated: true });
}
