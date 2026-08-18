from django.urls import path

from .views import StudentProgressReportView, SupervisorReviewReportView

urlpatterns = [
    path("student/progress/", StudentProgressReportView.as_view(), name="student-progress-report"),
    path("supervisor/reviews/", SupervisorReviewReportView.as_view(), name="supervisor-review-report"),
]
