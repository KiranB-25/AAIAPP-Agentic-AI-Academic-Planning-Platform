export type GoalStatus = "pending" | "plan_generated";

export interface AcademicGoal {
  id: number;
  subject: string;
  description: string;
  duration: number;
  intensity: string;
  status: GoalStatus;
  is_editable: boolean;
  created_at: string;
  updated_at: string;
}

export interface GoalCreateRequest {
  subject: string;
  description: string;
  duration: number;
  intensity?: string;
}

export type GoalUpdateRequest = Partial<GoalCreateRequest>;
