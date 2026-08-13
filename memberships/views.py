from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Membership, MembershipPlan, MembershipStatus, Visit, Payment
from users.permissions import IsTrainerOrAdmin, IsAdmin, IsClient
from .serializers import MembershipCreateSerializer, VisitCreateSerializer, MembershipSerializer, VisitSerializer, MembershipPlanSerializer, MembershipCancelSerializer, VisitCancelSerializer, PaymentSerializer, PaymentCreateSerializer

from datetime import datetime

from django.db.models import Count, Sum

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
        return Response(MembershipPlanSerializer(plan).data, status=status.HTTP_201_CREATED)


class MembershipCurrentView(APIView):
    serializer_class = MembershipSerializer

    def get(self, request):
        membership = Membership.objects.filter(client=request.user, status=MembershipStatus.ACTIVE).first()
        if not membership:
            return Response(None)
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
        return Response(VisitSerializer(visit).data)


class VisitListView(APIView):
    permission_classes = [IsClient]

    def get(self, request):
        visits = Visit.objects.filter(membership__client=request.user, cancelled_at__isnull=True).order_by('-marked_at')
        return Response(VisitSerializer(visits, many=True).data)

class PaymentListCreateView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request, pk):
        membership = get_object_or_404(Membership, pk=pk)
        payments = Payment.objects.filter(membership=membership).order_by('-paid_at')
        return Response(PaymentSerializer(payments, many=True).data)

    def post(self, request, pk):
        membership = get_object_or_404(Membership, pk=pk)
        serializer = PaymentCreateSerializer(
            data=request.data,
            context={'request': request, 'membership': membership},
        )
        serializer.is_valid(raise_exception=True)
        payment = serializer.save()
        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


class StatsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        if not date_from or not date_to:
            return Response(
                {'detail': 'Нужны date_from и date_to (YYYY-MM-DD)'},
                status=400,
                )

        date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
        date_to = datetime.strptime(date_to, '%Y-%m-%d').date()

        payments_qs = Payment.objects.filter(
            paid_at__gte=date_from,
            paid_at__lte=date_to,
        )
        payments_agg = payments_qs.aggregate(
            count=Count('id'),
            total_amount=Sum('amount'),
        )

        visits_count = Visit.objects.filter(
            marked_at__date__gte=date_from,
            marked_at__date__lte=date_to,
            cancelled_at__isnull=True,
        ).count()

        issued_count = Membership.objects.filter(
            issued_at__date__gte=date_from,
            issued_at__date__lte=date_to,
        ).count()
        cancelled_count = Membership.objects.filter(
            cancelled_at__date__gte=date_from,
            cancelled_at__date__lte=date_to,
        ).count()

        trainers_raw = (
            Visit.objects.filter(
                marked_at__date__gte=date_from,
                marked_at__date__lte=date_to,
                cancelled_at__isnull=True,
                marked_by__isnull=False,
            )
            .values('marked_by', 'marked_by__first_name', 'marked_by__last_name')
            .annotate(visits_marked=Count('id'))
            .order_by('-visits_marked')
        )
        trainers = [
            {
                'id': row['marked_by'],
                'full_name': f"{row['marked_by__first_name']} {row['marked_by__last_name']}".strip(),
                'visits_marked': row['visits_marked'],
            }
            for row in trainers_raw
        ]
        
        return Response({
            'date_from': str(date_from),
            'date_to': str(date_to),
            'payments': {
                'count': payments_agg['count'],
                'total_amount': payments_agg['total_amount'] or 0,
            },
            'visits': {
                'count': visits_count,
            },
            'memberships': {
                'issued_count': issued_count,
                'cancelled_count': cancelled_count,
            },
            'trainers': trainers,
        })