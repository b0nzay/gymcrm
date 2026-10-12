from datetime import datetime

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ActivityLog, User, log_activity
from .permissions import IsAdmin
from .serializers import ActivityLogSerializer, AdminUserSerializer, TrainerSerializer


class AdminUserListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        q = request.query_params.get('q', '').strip()
        users = User.objects.exclude(role=User.Role.ADMIN).order_by('role', 'last_name', 'first_name')

        if q:
            lookup = (
                Q(username__icontains=q)
                | Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
            )
            users = users.filter(lookup)

        return Response(AdminUserSerializer(users, many=True).data)


class AdminUserUpdateView(APIView):
    permission_classes = [IsAdmin]

    def patch(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if user.role == User.Role.ADMIN:
            return Response({'detail': 'Нельзя изменять администратора'}, status=400)

        old_role = user.role
        old_active = user.is_active

        serializer = AdminUserSerializer(
            user,
            data=request.data,
            partial=True,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        name = user.display_name

        if 'is_active' in request.data and user.is_active != old_active:
            log_activity(
                request.user,
                'user_activate' if user.is_active else 'user_deactivate',
                f'Пользователь {name}: is_active={user.is_active}',
            )

        if 'role' in request.data and user.role != old_role:
            log_activity(
                request.user,
                'user_role_change',
                f'Пользователь {name}: роль {old_role} → {user.role}',
            )

        return Response(AdminUserSerializer(user).data)


class TrainerListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        trainers = User.objects.filter(role=User.Role.TRAINER, is_active=True).order_by(
            'last_name', 'first_name'
        )
        return Response(TrainerSerializer(trainers, many=True).data)


class ActivityLogListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        logs = ActivityLog.objects.select_related('actor').all()

        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        time_from = request.query_params.get('time_from')
        time_to = request.query_params.get('time_to')

        if date_from:
            try:
                logs = logs.filter(created_at__date__gte=datetime.strptime(date_from, '%Y-%m-%d').date())
            except ValueError:
                return Response({'detail': 'Неверный date_from'}, status=400)

        if date_to:
            try:
                logs = logs.filter(created_at__date__lte=datetime.strptime(date_to, '%Y-%m-%d').date())
            except ValueError:
                return Response({'detail': 'Неверный date_to'}, status=400)

        if time_from:
            try:
                t = datetime.strptime(time_from, '%H:%M').time()
                logs = logs.filter(created_at__time__gte=t)
            except ValueError:
                return Response({'detail': 'Неверный time_from (HH:MM)'}, status=400)

        if time_to:
            try:
                t = datetime.strptime(time_to, '%H:%M').time()
                logs = logs.filter(created_at__time__lte=t)
            except ValueError:
                return Response({'detail': 'Неверный time_to (HH:MM)'}, status=400)

        return Response(ActivityLogSerializer(logs, many=True).data)
