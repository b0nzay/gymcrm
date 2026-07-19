from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.response import Response

from .models import Membership
from .permissions import IsTrainerOrAdmin
from .serializers import MembershipCreateSerializer, VisitCreateSerializer, MembershipSerializer, VisitSerializer

class MembershipCreateView(generics.CreateAPIView):
    serializer_class = MembershipCreateSerializer
    permission_classes = [IsTrainerOrAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership = serializer.save()
        return Response(
            MembershipSerializer(membership).data,
            status=status.HTTP_201_CREATED
        )

class VisitCreateView(generics.CreateAPIView):
    serializer_class = VisitCreateSerializer
    permission_classes = [IsTrainerOrAdmin]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['membership'] = get_object_or_404(Membership, pk=self.kwargs['pk'])
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        visit = serializer.save()
        return Response(
            VisitSerializer(visit).data,
            status=status.HTTP_201_CREATED
        )