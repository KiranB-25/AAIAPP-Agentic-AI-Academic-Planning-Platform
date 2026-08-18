from django.urls import path
from .views import NotificationListView, NotificationMarkReadView, NotificationUnreadCountView

urlpatterns = [path("", NotificationListView.as_view()), path("unread-count/", NotificationUnreadCountView.as_view()), path("<int:pk>/read/", NotificationMarkReadView.as_view())]
