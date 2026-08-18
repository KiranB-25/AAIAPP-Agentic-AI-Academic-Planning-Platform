# AI Orchestration Baseline

## Boundary

The approved AI architecture is server-side, API-based LLM integration under controlled orchestration. Users cannot directly invoke agents. AI API credentials remain in backend environment configuration and are never exposed to the frontend.

## Components

| Component | Approved responsibility |
| --- | --- |
| AgentOrchestrator | Coordinates ordered execution, workflow control, transactional consistency, and controlled persistence path |
| PlannerAgent | Decomposes a validated AcademicGoal into structured, time-bound milestones/subtasks |
| ContentGeneratorAgent | Enriches milestones into detailed activities, objectives, techniques, scheduling, and revision checkpoints |
| EvaluationAgent | Checks sequencing, feasibility, completeness, workload balance, logical consistency, and redundancy/inappropriate content |
| Plan Aggregation | Combines approved agent outputs into the consistently formatted StudyPlan structure |

## Required flow

```text
Student goal
  → API authentication, RBAC, and serializer validation
  → AgentOrchestrator
  → PlannerAgent
  → ContentGeneratorAgent
  → EvaluationAgent
  → Plan Aggregation
  → controlled Django ORM persistence
  → StudyPlan and PlanTask response
```

An invalid AI result is regenerated or returned as a structured error according to the SRS/SDD; incomplete plan data must not be persisted. Execution data is logged for transparency. Long-running work may be delegated to Celery/Redis where the SDD requires asynchronous processing, without changing the ordered agent sequence.

## Phase 0 status

No agents, prompts, LLM calls, background jobs, parsers, validators, or persistence code exist yet.

## Decision Required

- The SRS includes a `ValidationAgent` in one architectural overview, while the detailed SRS requirements and SDD define `EvaluationAgent`. Confirm whether ValidationAgent is a distinct future component or a naming overlap before creating an additional agent.
- The approved documents require structured output validation but do not define the LLM provider, response schema, retry count, or fallback behavior. These are implementation decisions requiring project-owner approval/configuration in Phase 4.
