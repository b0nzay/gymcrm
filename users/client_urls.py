from django.urls import path

from .views import ClientListView, ClientDetailView, ClientCreateView, StaffNoteListCreateView

urlpatterns = [
    path('', ClientListView.as_view(), name='client-list'),
    path('<int:pk>/', ClientDetailView.as_view(), name='client-detail'),
    path('create/', ClientCreateView.as_view(), name='client-create'),
    path('<int:pk>/notes/', StaffNoteListCreateView.as_view(), name='staff-notes')
]