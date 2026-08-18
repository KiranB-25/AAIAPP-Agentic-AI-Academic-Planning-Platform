from django.urls import path

from .views import AcademicGoalDetailView, AcademicGoalListCreateView

urlpatterns = [
    path("", AcademicGoalListCreateView.as_view(), name="goal-list-create"),
    path("<int:pk>/", AcademicGoalDetailView.as_view(), name="goal-detail"),
]
