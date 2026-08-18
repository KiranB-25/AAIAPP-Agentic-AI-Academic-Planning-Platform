from django.urls import path
from .views import SupervisorPlanDetailView, SupervisorPlanListView, SupervisorReviewHistoryView, SupervisorReviewView, StudentReviewListView

urlpatterns = [
    path("supervisor/plans/", SupervisorPlanListView.as_view()),
    path("supervisor/plans/<int:pk>/", SupervisorPlanDetailView.as_view()),
    path("supervisor/plans/<int:pk>/review/", SupervisorReviewView.as_view()),
    path("supervisor/reviews/", SupervisorReviewHistoryView.as_view()),
    path("student/reviews/", StudentReviewListView.as_view()),
]
