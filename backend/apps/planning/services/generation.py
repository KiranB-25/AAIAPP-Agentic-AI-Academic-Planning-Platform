import uuid

from ..models import StudyPlan
from .orchestration import AgentOrchestrator
from .persistence import StudyPlanPersistenceService


class StudyPlanGenerationService:
    """Application boundary joining agent orchestration to atomic persistence."""

    def __init__(self, orchestrator: AgentOrchestrator, persistence: StudyPlanPersistenceService):
        self.orchestrator = orchestrator
        self.persistence = persistence

    def generate(self, *, goal, actor, request_id: uuid.UUID) -> StudyPlan:
        aggregated_plan, evaluation = self.orchestrator.run_for_persistence(goal)
        return self.persistence.persist(
            goal=goal,
            actor=actor,
            request_id=request_id,
            aggregated_plan=aggregated_plan,
            evaluation=evaluation,
        )
