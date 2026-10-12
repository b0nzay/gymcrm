from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Membership, MembershipPlan, MembershipStatus, Visit, Payment
from users.permissions import IsTrainerOrAdmin, IsAdmin, IsClient
from users.models import User, log_activity
from .serializers import (
    MembershipCreateSerializer,
    VisitCreateSerializer,
    MembershipSerializer,
    VisitSerializer,
    MembershipPlanSerializer,
    MembershipCancelSerializer,
    VisitCancelSerializer,
    PaymentSerializer,
    PaymentCreateSerializer,
    AdminMembershipSerializer,
)

from datetime import datetime

from django.db.models import Count, Sum, Prefetch


def _filter_by_date(qs, field, date_from, date_to):
    if date_from:
        qs = qs.filter(**{f'{field}__date__gte': date_from})
    if date_to:
        qs = qs.filter(**{f'{field}__date__lte': date_to})
    return qs


def _staff_name(first_name, last_name, username):
    return f'{first_name} {last_name}'.strip() or username


def _count_by_trainer(qs, user_field):
    rows = (
        qs.filter(**{
            f'{user_field}__isnull': False,
            f'{user_field}__role': User.Role.TRAINER,
        })
        .values(
            user_field,
            f'{user_field}__first_name',
            f'{user_field}__last_name',
            f'{user_field}__username',
        )
        .annotate(total=Count('id'))
    )
    by_id = {}
    for row in rows:
        uid = row[user_field]
        by_id[uid] = {
            'id': uid,
            'full_name': _staff_name(
                row[f'{user_field}__first_name'],
                row[f'{user_field}__last_name'],
                row[f'{user_field}__username'],
            ),
            'total': row['total'],
        }
    return by_id


def _merge_trainer_counts(left, right, left_key, right_key):
    items = []
    for uid in set(left) | set(right):
        a = left.get(uid) or {}
        b = right.get(uid) or {}
        items.append({
            'id': uid,
            'full_name': a.get('full_name') or b.get('full_name') or '',
            left_key: a.get('total', 0),
            right_key: b.get('total', 0),
        })
    items.sort(key=lambda row: (-(row[left_key] + row[right_key]), row['full_name']))
    return items


def _ensure_trainer_row(items, trainer, extra):
    if not trainer:
        return items
    if any(row['id'] == trainer.id for row in items):
        return items
    name = _staff_name(trainer.first_name, trainer.last_name, trainer.username)
    return [{'id': trainer.id, 'full_name': name, **extra}, *items]


class MembershipCreateView(generics.CreateAPIView):
    serializer_class = MembershipCreateSerializer
    permission_classes = [IsTrainerOrAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership = serializer.save()
        client_name = f'{membership.client.first_name} {membership.client.last_name}'.strip() or membership.client.username
        log_activity(
            request.user,
            'membership_issue',
            f'Выдан абонемент #{membership.id} клиенту {client_name} ({membership.plan.name})',
        )
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
        client = visit.membership.client
        client_name = f'{client.first_name} {client.last_name}'.strip() or client.username
        log_activity(
            request.user,
            'visit_mark',
            f'Отмечено посещение #{visit.id} клиента {client_name}',
        )
        return Response(
            VisitSerializer(visit).data,
            status=status.HTTP_201_CREATED
        )


class MembershipPlanView(APIView):
    serializer_class = MembershipPlanSerializer

    def get(self, request):
        plans = MembershipPlan.objects.filter(is_active=True).order_by("sort_order")
        return Response(MembershipPlanSerializer(plans, many=True).data)


class MembershipPlanCreateView(generics.CreateAPIView):
    serializer_class = MembershipPlanSerializer
    permission_classes = [IsAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        plan = serializer.save()
        log_activity(request.user, 'plan_create', f'Создан план «{plan.name}» (#{plan.id})')
        return Response(MembershipPlanSerializer(plan).data, status=status.HTTP_201_CREATED)


class MembershipPlanDetailView(APIView):
    permission_classes = [IsAdmin]

    def patch(self, request, pk):
        plan = get_object_or_404(MembershipPlan, pk=pk)
        if not plan.is_active:
            return Response({'detail': 'Архивный план нельзя редактировать'}, status=400)

        was_active = plan.is_active
        serializer = MembershipPlanSerializer(plan, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        plan = serializer.save()

        if was_active and not plan.is_active:
            log_activity(request.user, 'plan_archive', f'План «{plan.name}» (#{plan.id}) архивирован')
        else:
            log_activity(request.user, 'plan_update', f'Обновлён план «{plan.name}» (#{plan.id})')

        return Response(MembershipPlanSerializer(plan).data)


class MembershipCurrentView(APIView):
    serializer_class = MembershipSerializer

    def get(self, request):
        Membership.sync_overdue(client=request.user)
        membership = Membership.objects.filter(client=request.user, status=MembershipStatus.ACTIVE).first()
        if not membership:
            return Response(status=204)
        return Response(MembershipSerializer(membership).data)


class MembershipCancelView(APIView):
    permission_classes = [IsTrainerOrAdmin]

    def post(self, request, pk):
        membership = get_object_or_404(Membership, pk=pk)
        serializer = MembershipCancelSerializer(
            membership,
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        membership = serializer.save()
        client_name = f'{membership.client.first_name} {membership.client.last_name}'.strip() or membership.client.username
        log_activity(
            request.user,
            'membership_cancel',
            f'Отменён абонемент #{membership.id} клиента {client_name}',
        )
        return Response(MembershipSerializer(membership).data)


class VisitCancelView(APIView):
    permission_classes = [IsTrainerOrAdmin]

    def post(self, request, pk):
        visit = get_object_or_404(Visit, pk=pk)
        serializer = VisitCancelSerializer(
            visit,
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        visit = serializer.save()
        client = visit.membership.client
        client_name = f'{client.first_name} {client.last_name}'.strip() or client.username
        log_activity(
            request.user,
            'visit_cancel',
            f'Отменено посещение #{visit.id} клиента {client_name}',
        )
        return Response(VisitSerializer(visit).data)


class VisitListView(APIView):
    permission_classes = [IsClient]

    def get(self, request):
        visits = Visit.objects.filter(membership__client=request.user, cancelled_at__isnull=True).order_by('-marked_at')
        return Response(VisitSerializer(visits, many=True).data)


class PaymentListCreateView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        membership = get_object_or_404(Membership, pk=pk)
        serializer = PaymentCreateSerializer(
            data=request.data,
            context={'request': request, 'membership': membership},
        )
        serializer.is_valid(raise_exception=True)
        payment = serializer.save()
        client_name = f'{membership.client.first_name} {membership.client.last_name}'.strip() or membership.client.username
        log_activity(
            request.user,
            'payment_create',
            f'Оплата {payment.amount} руб. по абонементу #{membership.id} ({client_name})',
        )
        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


class PaymentDetailView(APIView):
    permission_classes = [IsAdmin]

    def patch(self, request, pk):
        payment = get_object_or_404(Payment, pk=pk)
        serializer = PaymentCreateSerializer(
            payment,
            data=request.data,
            context={'request': request, 'membership': payment.membership},
        )
        serializer.is_valid(raise_exception=True)
        payment = serializer.save()
        log_activity(
            request.user,
            'payment_update',
            f'Изменена оплата #{payment.id} ({payment.amount} руб.) по абонементу #{payment.membership_id}',
        )
        return Response(PaymentSerializer(payment).data)

    def delete(self, request, pk):
        payment = get_object_or_404(Payment, pk=pk)
        membership_id = payment.membership_id
        amount = payment.amount
        payment_id = payment.id
        payment.delete()
        log_activity(
            request.user,
            'payment_delete',
            f'Удалена оплата #{payment_id} ({amount} руб.) по абонементу #{membership_id}',
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminMembershipListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        Membership.sync_overdue()
        memberships = (
            Membership.objects
            .select_related('client', 'plan', 'issued_by')
            .prefetch_related(Prefetch('payment_set', queryset=Payment.objects.order_by('-paid_at')))
            .order_by('-issued_at')
        )
        return Response(AdminMembershipSerializer(memberships, many=True).data)


class StatsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        Membership.sync_overdue()
        date_from_raw = request.query_params.get('date_from') or ''
        date_to_raw = request.query_params.get('date_to') or ''
        trainer_id = request.query_params.get('trainer_id')
        event_type = request.query_params.get('type', '').strip()

        date_from = None
        date_to = None
        if date_from_raw:
            try:
                date_from = datetime.strptime(date_from_raw, '%Y-%m-%d').date()
            except ValueError:
                return Response({'detail': 'Неверный формат date_from'}, status=400)
        if date_to_raw:
            try:
                date_to = datetime.strptime(date_to_raw, '%Y-%m-%d').date()
            except ValueError:
                return Response({'detail': 'Неверный формат date_to'}, status=400)

        if event_type and event_type not in ('membership', 'visit'):
            return Response({'detail': 'type: membership или visit'}, status=400)

        trainer = None
        if trainer_id:
            try:
                trainer = User.objects.get(pk=int(trainer_id), role=User.Role.TRAINER)
            except (User.DoesNotExist, ValueError):
                return Response({'detail': 'Тренер не найден'}, status=400)

        payments_qs = Payment.objects.all()
        if date_from:
            payments_qs = payments_qs.filter(paid_at__gte=date_from)
        if date_to:
            payments_qs = payments_qs.filter(paid_at__lte=date_to)

        payments_agg = payments_qs.aggregate(
            count=Count('id'),
            total_amount=Sum('amount'),
        )

        issued_qs = _filter_by_date(Membership.objects.all(), 'issued_at', date_from, date_to)
        cancelled_memberships_qs = _filter_by_date(
            Membership.objects.filter(cancelled_at__isnull=False),
            'cancelled_at',
            date_from,
            date_to,
        )
        if trainer:
            issued_qs = issued_qs.filter(issued_by=trainer)
            cancelled_memberships_qs = cancelled_memberships_qs.filter(cancelled_by=trainer)

        visits_qs = _filter_by_date(
            Visit.objects.filter(cancelled_at__isnull=True),
            'marked_at',
            date_from,
            date_to,
        )
        cancelled_visits_qs = _filter_by_date(
            Visit.objects.filter(cancelled_at__isnull=False),
            'cancelled_at',
            date_from,
            date_to,
        )
        if trainer:
            visits_qs = visits_qs.filter(marked_by=trainer)
            cancelled_visits_qs = cancelled_visits_qs.filter(cancelled_by=trainer)

        memberships_by_trainer = _ensure_trainer_row(
            _merge_trainer_counts(
                _count_by_trainer(issued_qs, 'issued_by'),
                _count_by_trainer(cancelled_memberships_qs, 'cancelled_by'),
                'issued',
                'cancelled',
            ),
            trainer,
            {'issued': 0, 'cancelled': 0},
        )
        visits_by_trainer = _ensure_trainer_row(
            _merge_trainer_counts(
                _count_by_trainer(visits_qs, 'marked_by'),
                _count_by_trainer(cancelled_visits_qs, 'cancelled_by'),
                'marked',
                'cancelled',
            ),
            trainer,
            {'marked': 0, 'cancelled': 0},
        )

        items = []

        if event_type in ('', 'membership'):
            memberships_qs = Membership.objects.select_related('client', 'plan', 'issued_by')
            if date_from:
                memberships_qs = memberships_qs.filter(issued_at__date__gte=date_from)
            if date_to:
                memberships_qs = memberships_qs.filter(issued_at__date__lte=date_to)
            if trainer:
                memberships_qs = memberships_qs.filter(issued_by=trainer)

            for m in memberships_qs.order_by('-issued_at'):
                client_name = f'{m.client.first_name} {m.client.last_name}'.strip() or m.client.username
                issuer = None
                if m.issued_by:
                    issuer = f'{m.issued_by.first_name} {m.issued_by.last_name}'.strip() or m.issued_by.username
                items.append({
                    'type': 'membership',
                    'id': m.id,
                    'at': m.issued_at.isoformat(),
                    'client_name': client_name,
                    'plan_name': m.plan.name if m.plan else None,
                    'status': m.status,
                    'issued_by_name': issuer,
                    'price_list': m.price_list,
                })

        if event_type in ('', 'visit'):
            for v in visits_qs.select_related('membership__client', 'membership__plan', 'marked_by').order_by('-marked_at'):
                client = v.membership.client
                client_name = f'{client.first_name} {client.last_name}'.strip() or client.username
                marker = None
                if v.marked_by:
                    marker = f'{v.marked_by.first_name} {v.marked_by.last_name}'.strip() or v.marked_by.username
                items.append({
                    'type': 'visit',
                    'id': v.id,
                    'at': v.marked_at.isoformat(),
                    'client_name': client_name,
                    'plan_name': v.membership.plan.name if v.membership.plan else None,
                    'marked_by_name': marker,
                    'notes': v.notes,
                })

        items.sort(key=lambda x: x['at'], reverse=True)

        return Response({
            'date_from': str(date_from) if date_from else None,
            'date_to': str(date_to) if date_to else None,
            'summary': {
                'payments_total': payments_agg['total_amount'] or 0,
                'payments_count': payments_agg['count'] or 0,
                'memberships_issued': issued_qs.count(),
                'memberships_cancelled': cancelled_memberships_qs.count(),
                'memberships_ended': issued_qs.filter(
                    status__in=[MembershipStatus.EXPIRED, MembershipStatus.DEPLETED]
                ).count(),
                'visits_count': visits_qs.count(),
                'visits_cancelled': cancelled_visits_qs.count(),
                'memberships_by_trainer': memberships_by_trainer,
                'visits_by_trainer': visits_by_trainer,
            },
            'items': items,
        })


class MembershipListView(APIView):
    permission_classes = [IsClient]

    def get(self, request):
        Membership.sync_overdue(client=request.user)
        memberships = Membership.objects.filter(client=request.user).order_by('-issued_at')
        return Response(MembershipSerializer(memberships, many=True).data)
