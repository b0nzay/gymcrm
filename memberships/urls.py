from django.urls import path

from .views import (
    MembershipCreateView,
    VisitCreateView,
    MembershipPlanView,
    MembershipPlanCreateView,
    MembershipPlanDetailView,
    MembershipCurrentView,
    MembershipCancelView,
    VisitCancelView,
    VisitListView,
    PaymentListCreateView,
    PaymentDetailView,
    MembershipListView,
    AdminMembershipListView,
)

urlpatterns = [
    path('admin/', AdminMembershipListView.as_view(), name='admin-memberships'),
    path('plans/', MembershipPlanView.as_view(), name='membership-plans'),
    path('plans/create/', MembershipPlanCreateView.as_view(), name='membership-plans-create'),
    path('plans/<int:pk>/', MembershipPlanDetailView.as_view(), name='membership-plans-detail'),
    path('current/', MembershipCurrentView.as_view(), name='membership-current'),
    path('my/', MembershipListView.as_view(), name='memberships-list'),
    path('my/visits/', VisitListView.as_view(), name='visit-list'),
    path('visits/<int:pk>/cancel/', VisitCancelView.as_view(), name='visit-cancel'),
    path('payments/<int:pk>/', PaymentDetailView.as_view(), name='payment-detail'),
    path('', MembershipCreateView.as_view(), name='membership-create'),
    path('<int:pk>/visits/', VisitCreateView.as_view(), name='visit-create'),
    path('<int:pk>/cancel/', MembershipCancelView.as_view(), name='membership-cancel'),
    path('<int:pk>/payments/', PaymentListCreateView.as_view(), name='payments'),
]
