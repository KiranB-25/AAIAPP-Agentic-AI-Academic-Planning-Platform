export interface PlanTask {
  id: number;
  week: number;
  title: string;
  description: string;
  method: string;
  objective: string;
  revision_checkpoint: boolean;
  is_completed: boolean;
  completed_at: string | null;
  updated_at: string;
}

export interface PlanTaskCompletionUpdate {
  task: PlanTask;
  progress: number;
}

export interface StudyPlan {
  id: number;
  goal_id: number;
  generated_at: string;
  summary: string;
  status: "generated" | "approved" | "revision_required";
  progress: number;
  tasks: PlanTask[];
}
