from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView

from django.db.models import Q
from django.shortcuts import get_object_or_404

from .serializers import RegisterSerializer, LoginSerializer, UserSerializer, AccessCodeSerializer, AccessCodeRotateSerializer, ClientCreateSerializer, StaffNoteSerializer, StaffNoteCreateSerializer
from .permissions import IsAdmin, IsTrainerOrAdmin
from .models import AccessCode, User, StaffNote

from memberships.models import Membership, Visit
from memberships.serializers import MembershipSerializer, VisitSerializer


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            },
            status=status.HTTP_201_CREATED
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer_class = LoginSerializer(data=request.data)
        serializer_class.is_valid(raise_exception=True)
        user = serializer_class.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            },
            status=status.HTTP_200_OK
        )


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    http_method_names = ['get', 'patch', 'head', 'options']

    def get_object(self):
        return self.request.user


class AccessCodeCurrentView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        active = AccessCode.get_active()
        if not active:
            return Response({'detail': 'Активного кода нет'}, status=404)
        return Response(AccessCodeSerializer(active).data)


class AccessCodeRotateView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = AccessCodeRotateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        access_code = serializer.save()
        from users.models import log_activity
        log_activity(request.user, 'access_code_rotate', f'Новый код доступа: {access_code.code}')
        return Response(AccessCodeSerializer(access_code).data, status=200)


class ClientListView(APIView):
    permission_classes = [IsTrainerOrAdmin]

    def get(self, request):
        q = request.query_params.get('q', '').strip()
        clients = User.objects.filter(role=User.Role.CLIENT)

        if q != '':
            lookup = (
                Q(username__icontains=q)
                | Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
            )
            clients = clients.filter(lookup)

        return Response(UserSerializer(clients, many=True).data)


class ClientDetailView(APIView):
    permission_classes = [IsTrainerOrAdmin]

    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk, role=User.Role.CLIENT)
        Membership.sync_overdue(client=user)
        memberships = Membership.objects.filter(client=user).order_by('-issued_at')
        visits = Visit.objects.filter(membership__client=user).order_by('-marked_at')
        notes = StaffNote.objects.filter(client=user).order_by('-created_at')
        return Response({"user": UserSerializer(user).data,"memberships": MembershipSerializer(memberships, many=True).data,"visits": VisitSerializer(visits, many=True).data, "notes": StaffNoteSerializer(notes, many=True).data})

    def patch(self, request, pk):
        user = get_object_or_404(User, pk=pk, role=User.Role.CLIENT)
        serializer = UserSerializer(user, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(user).data)


class ClientCreateView(generics.CreateAPIView):
    permission_classes = [IsTrainerOrAdmin]
    serializer_class = ClientCreateSerializer 

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(UserSerializer(user).data,status=status.HTTP_201_CREATED)


class StaffNoteListCreateView(APIView):
    permission_classes = [IsTrainerOrAdmin]

    def post(self, request, pk):
        client = get_object_or_404(User, pk=pk, role=User.Role.CLIENT)
        serializer = StaffNoteCreateSerializer(
            data=request.data,
            context={'request': request, 'client': client},
        )
        serializer.is_valid(raise_exception=True)
        note = serializer.save()
        return Response(StaffNoteSerializer(note).data, status=status.HTTP_201_CREATED)