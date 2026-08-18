from django.urls import path

from .views import PlanExportView, SupervisorPlanExportView

urlpatterns = [
    path("plans/<int:pk>/", PlanExportView.as_view(), name="student-plan-export"),
    path("supervisor/plans/<int:pk>/", SupervisorPlanExportView.as_view(), name="supervisor-plan-export"),
]
