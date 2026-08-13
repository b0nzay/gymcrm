from django.urls import path

from .views import MembershipCreateView, VisitCreateView, MembershipPlanView, MembershipPlanCreateView, MembershipCurrentView, MembershipCancelView, VisitCancelView, VisitListView, PaymentListCreateView

urlpatterns = [
    path('', MembershipCreateView.as_view(), name='membership-create'),
    path('<int:pk>/visits/', VisitCreateView.as_view(), name='visit-create'),
    path('plans/', MembershipPlanView.as_view(), name='membership-plans'),
    path('plans/create/', MembershipPlanCreateView.as_view(), name='membership-plans-create'),
    path('current/', MembershipCurrentView.as_view(), name='membership-current'),
    path('<int:pk>/cancel/', MembershipCancelView.as_view(), name='membership-cancel'),
    path('visits/<int:pk>/cancel/', VisitCancelView.as_view(), name='visit-cancel'),
    path('my/visits/', VisitListView.as_view(), name='visit-list'),
    path('<int:pk>/payments/', PaymentListCreateView.as_view(), name='payments')
]