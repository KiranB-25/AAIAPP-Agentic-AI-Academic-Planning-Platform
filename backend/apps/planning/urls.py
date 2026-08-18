from django.urls import path

from .views import GenerateStudyPlanView, PlanTaskDetailView, StudyPlanDetailView, StudyPlanListView

urlpatterns = [
    path("", StudyPlanListView.as_view(), name="plan-list"),
    path("<int:pk>/", StudyPlanDetailView.as_view(), name="plan-detail"),
    path("tasks/<int:pk>/", PlanTaskDetailView.as_view(), name="plan-task-detail"),
    path("goals/<int:goal_id>/generate/", GenerateStudyPlanView.as_view(), name="plan-generate"),
]
