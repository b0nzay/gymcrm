from django.urls import path

from .views import MembershipCreateView, VisitCreateView

urlpatterns = [
    path('', MembershipCreateView.as_view(), name='membership-create'),
    path('<int:pk>/visits/', VisitCreateView.as_view(), name='visit-create'),
]