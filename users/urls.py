from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import RegisterView, LoginView, MeView, AccessCodeCurrentView, AccessCodeRotateView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth-register'),
    path('login/', LoginView.as_view(), name='auth-login'),
    path('me/', MeView.as_view(), name='auth-me'),
    path('refresh/', TokenRefreshView.as_view(), name='auth-refresh'),
    path('access-code/', AccessCodeCurrentView.as_view(), name='access-code-current'),
    path('access-code/rotate/', AccessCodeRotateView.as_view(), name='access-code-rotate')
]