from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsStudent, IsSupervisor
from apps.planning.models import StudyPlan
from apps.planning.serializers import StudyPlanSerializer

from .models import PlanReview
from .serializers import PlanReviewSerializer, ReviewSubmissionSerializer
from .services import ReviewWorkflowService


class SupervisorPlanListView(generics.ListAPIView):
    permission_classes = (IsSupervisor,)
    serializer_class = StudyPlanSerializer
    def get_queryset(self):
        return StudyPlan.objects.filter(goal__owner__supervisor=self.request.user).select_related("goal", "goal__owner").prefetch_related("tasks")


class SupervisorPlanDetailView(SupervisorPlanListView, generics.RetrieveAPIView):
    pass


class SupervisorReviewView(APIView):
    permission_classes = (IsSupervisor,)
    def post(self, request, pk):
        plan = StudyPlan.objects.select_related("goal__owner", "goal__owner__supervisor").filter(goal__owner__supervisor=request.user, pk=pk).first()
        if plan is None:
            return Response({"detail": "Study plan not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = ReviewSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = ReviewWorkflowService.submit(plan=plan, supervisor=request.user, **serializer.validated_data)
        return Response(PlanReviewSerializer(review).data, status=status.HTTP_201_CREATED)


class SupervisorReviewHistoryView(generics.ListAPIView):
    permission_classes = (IsSupervisor,)
    serializer_class = PlanReviewSerializer
    def get_queryset(self):
        return PlanReview.objects.filter(study_plan__goal__owner__supervisor=self.request.user).select_related("study_plan")


class StudentReviewListView(generics.ListAPIView):
    permission_classes = (IsStudent,)
    serializer_class = PlanReviewSerializer
    def get_queryset(self):
        return PlanReview.objects.filter(study_plan__goal__owner=self.request.user).select_related("study_plan")
