from django.urls import path

from .admin_views import (
    AdminUserListView,
    AdminUserUpdateView,
    TrainerListView,
    ActivityLogListView,
)

urlpatterns = [
    path('trainers/', TrainerListView.as_view(), name='trainer-list'),
    path('logs/', ActivityLogListView.as_view(), name='activity-log-list'),
    path('', AdminUserListView.as_view(), name='admin-user-list'),
    path('<int:pk>/', AdminUserUpdateView.as_view(), name='admin-user-update'),
]
