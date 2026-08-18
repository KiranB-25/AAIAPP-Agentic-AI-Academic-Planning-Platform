import uuid

from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsStudent
from apps.audit.models import AuditLog
from apps.audit.services import record
from apps.goals.models import AcademicGoal

from .agents import DeterministicContentGeneratorAgent, DeterministicEvaluationAgent, DeterministicPlannerAgent
from .models import PlanTask, StudyPlan
from .serializers import (
    PlanTaskCompletionResponseSerializer,
    PlanTaskCompletionSerializer,
    PlanTaskSerializer,
    StudyPlanSerializer,
)
from .services import AgentOrchestrator, PlanAggregator, StudyPlanGenerationService, StudyPlanPersistenceService
from .services.exceptions import DuplicateStudyPlan, GoalNotEligible, OrchestrationError, PlanPersistenceError
from .services.progress import calculate_plan_progress


def generation_service():
    orchestrator = AgentOrchestrator(
        DeterministicPlannerAgent(),
        DeterministicContentGeneratorAgent(),
        DeterministicEvaluationAgent(),
        PlanAggregator(),
    )
    return StudyPlanGenerationService(orchestrator, StudyPlanPersistenceService())


class StudentPlanQuerysetMixin:
    permission_classes = (IsStudent,)
    serializer_class = StudyPlanSerializer

    def get_queryset(self):
        return StudyPlan.objects.filter(goal__owner=self.request.user).select_related("goal").prefetch_related("tasks")


class StudyPlanListView(StudentPlanQuerysetMixin, generics.ListAPIView):
    pass


class StudyPlanDetailView(StudentPlanQuerysetMixin, generics.RetrieveAPIView):
    pass


class PlanTaskDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsStudent,)
    http_method_names = ("get", "patch", "head", "options")

    def get_queryset(self):
        return PlanTask.objects.filter(plan__goal__owner=self.request.user).select_related("plan", "plan__goal")

    def get_serializer_class(self):
        return PlanTaskCompletionSerializer if self.request.method == "PATCH" else PlanTaskSerializer

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        record(
            actor=request.user,
            action=AuditLog.Action.TASK_COMPLETION_CHANGED,
            description=f"Set task #{instance.pk} completion to {instance.is_completed}.",
            request=request,
        )
        payload = {
            "task": PlanTaskSerializer(instance).data,
            "progress": calculate_plan_progress(instance.plan.tasks.all()),
        }
        return Response(PlanTaskCompletionResponseSerializer(payload).data)


class GenerateStudyPlanView(APIView):
    permission_classes = (IsStudent,)

    def post(self, request, goal_id):
        goal = get_object_or_404(AcademicGoal.objects.filter(owner=request.user), pk=goal_id)
        existing = StudyPlan.objects.filter(goal=goal).prefetch_related("tasks").first()
        if existing is not None:
            return Response(StudyPlanSerializer(existing).data, status=status.HTTP_200_OK)
        raw_request_id = request.data.get("request_id")
        try:
            request_id = uuid.UUID(str(raw_request_id))
        except (TypeError, ValueError, AttributeError):
            raise ValidationError({"request_id": ["A valid UUID request identifier is required."]})
        try:
            plan = generation_service().generate(goal=goal, actor=request.user, request_id=request_id)
        except DuplicateStudyPlan:
            existing = StudyPlan.objects.filter(goal=goal).prefetch_related("tasks").first()
            if existing is not None:
                return Response(StudyPlanSerializer(existing).data, status=status.HTTP_200_OK)
            return Response({"detail": "A study plan already exists for this goal."}, status=status.HTTP_409_CONFLICT)
        except GoalNotEligible:
            return Response({"detail": "This academic goal is not eligible for plan generation."}, status=status.HTTP_409_CONFLICT)
        except PlanPersistenceError:
            return Response(
                {"detail": "The study plan could not be saved. Please try again."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except OrchestrationError:
            return Response({"detail": "The study plan could not be generated. Please try again."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(StudyPlanSerializer(plan).data, status=status.HTTP_201_CREATED)
