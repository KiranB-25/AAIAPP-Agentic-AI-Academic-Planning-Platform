class OrchestrationError(RuntimeError):
    """Base exception for controlled planning workflow failures."""


class AgentExecutionError(OrchestrationError):
    def __init__(self, stage: str, message: str):
        self.stage = stage
        super().__init__(message)


class PlannerInputError(AgentExecutionError):
    """Raised when an AcademicGoal cannot be accepted by the Planner."""

    def __init__(self, message: str):
        super().__init__("planner", message)


class InfeasiblePlanningError(PlannerInputError):
    """Raised when valid Planner constraints cannot form a schedule."""


class ContentGenerationInputError(AgentExecutionError):
    """Raised when Planner output cannot be consumed by Content Generation."""

    def __init__(self, message: str):
        super().__init__("content_generator", message)


class InvalidAgentOutput(AgentExecutionError):
    pass


class EvaluationRejected(OrchestrationError):
    def __init__(self, issues: tuple[str, ...]):
        self.issues = issues
        super().__init__("The generated plan failed evaluation.")


class AggregationError(OrchestrationError):
    pass


class FinalPlanValidationError(OrchestrationError):
    pass


class PlanPersistenceError(OrchestrationError):
    pass


class GoalNotEligible(PlanPersistenceError):
    pass


class UnauthorizedGoalAccess(PlanPersistenceError):
    pass


class DuplicateStudyPlan(PlanPersistenceError):
    pass
