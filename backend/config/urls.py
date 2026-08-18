from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/goals/", include("apps.goals.urls")),
    path("api/plans/", include("apps.planning.urls")),
    path("api/reviews/", include("apps.reviews.urls")),
    path("api/notifications/", include("apps.notifications.urls")),
    path("api/audit/", include("apps.audit.urls")),
    path("api/exports/", include("apps.exports.urls")),
    path("api/reports/", include("apps.reports.urls")),
    path("api/", include("apps.api.urls")),
]
