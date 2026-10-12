from rest_framework import serializers

from .models import MembershipPlan, Membership, Visit, MembershipStatus, Payment
from users.models import User

from datetime import timedelta

from django.db import transaction
from django.utils import timezone


class MembershipPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipPlan
        fields = ['id', 'name', 'visits_total', 'validity_days', 'price_list', 'sort_order', 'notes', 'is_active']
        read_only_fields = ['id']
        extra_kwargs = {
            'is_active': {'required': False},
        }


class PaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Payment
        fields = ['id', 'membership', 'amount', 'paid_at', 'transaction_id', 'payer_name', 'created_at', 'comment']
        read_only_fields = fields


class MembershipSerializer(serializers.ModelSerializer):
    issued_by_name = serializers.SerializerMethodField()
    cancelled_by_name  = serializers.SerializerMethodField()
    plan = MembershipPlanSerializer(read_only=True)

    class Meta:
        model = Membership
        fields = ['id', 'client', 'plan', 'issued_by', 'issued_at', 'valid_until', 'visits_total', 'visits_remaining', 'price_list', 'status', 'notes', 'cancelled_at', 'cancelled_by', 'cancel_reason', 'issued_by_name', 'cancelled_by_name']
        read_only_fields = fields

    def get_issued_by_name(self, obj):
        if not obj.issued_by:
            return None
        return obj.issued_by.display_name
    
    def get_cancelled_by_name(self, obj):
        if not obj.cancelled_by:
            return None
        return obj.cancelled_by.display_name


class AdminMembershipSerializer(serializers.ModelSerializer):
    issued_by_name = serializers.SerializerMethodField()
    client_name = serializers.SerializerMethodField()
    client_username = serializers.SerializerMethodField()
    plan = MembershipPlanSerializer(read_only=True)
    payments = PaymentSerializer(source='payment_set', many=True, read_only=True)
    is_paid = serializers.SerializerMethodField()
    paid_amount = serializers.SerializerMethodField()

    class Meta:
        model = Membership
        fields = [
            'id', 'client', 'client_name', 'client_username', 'plan', 'issued_by',
            'issued_by_name', 'issued_at', 'valid_until', 'visits_total',
            'visits_remaining', 'price_list', 'status', 'notes',
            'payments', 'is_paid', 'paid_amount',
        ]
        read_only_fields = fields

    def get_issued_by_name(self, obj):
        if not obj.issued_by:
            return None
        return obj.issued_by.display_name

    def get_client_name(self, obj):
        return obj.client.display_name

    def get_client_username(self, obj):
        return obj.client.username

    def get_is_paid(self, obj):
        return obj.payment_set.exists()

    def get_paid_amount(self, obj):
        total = sum(p.amount for p in obj.payment_set.all())
        return total if total else None


class MembershipCreateSerializer(serializers.Serializer):
    client_id = serializers.IntegerField()
    plan_id = serializers.IntegerField()
    notes = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_client_id(self, value):
        try:
            client = User.objects.get(pk=value)
        except User.DoesNotExist:
            raise serializers.ValidationError('Клиент не найден')
        if client.role != User.Role.CLIENT:
            raise serializers.ValidationError('Пользователь не является клиентом')
        return value

    def validate_plan_id(self, value):
        if not MembershipPlan.objects.filter(pk=value, is_active=True).exists():
            raise serializers.ValidationError('План не найден или не активен')
        return value

    def validate(self, attrs):
        client = User.objects.get(pk=attrs['client_id'])
        Membership.sync_overdue(client=client)
        if Membership.objects.filter(client=client, status=MembershipStatus.ACTIVE).exists():
            raise serializers.ValidationError('У клиента уже есть активный абонемент')
        return attrs

    def create(self, validated_data):
        client = User.objects.get(pk=validated_data['client_id'])
        plan = MembershipPlan.objects.get(pk=validated_data['plan_id'])
        request = self.context['request']
        today = timezone.localdate()

        return Membership.objects.create(
            client=client,
            plan=plan,
            issued_by=request.user,
            valid_until=today + timedelta(days=plan.validity_days),
            visits_total=plan.visits_total,
            visits_remaining=plan.visits_total,
            price_list=plan.price_list,
            status=MembershipStatus.ACTIVE,
            notes=validated_data.get('notes', ''))


class VisitSerializer(serializers.ModelSerializer):
    marked_by_name = serializers.SerializerMethodField()
    cancelled_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Visit
        fields = ['id', 'membership', 'marked_by', 'marked_by_name', 'marked_at', 'notes', 'cancelled_at', 'cancelled_by', 'cancel_reason', 'cancelled_by_name']
        read_only_fields = fields

    def get_marked_by_name(self, obj):
        if not obj.marked_by:
            return None
        return obj.marked_by.display_name

    def get_cancelled_by_name(self, obj):
        if not obj.cancelled_by:
            return None
        return obj.cancelled_by.display_name


class VisitCreateSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, allow_blank=True, default='')
    
    def validate(self, attrs):
        membership = self.context['membership']
        Membership.sync_overdue(client=membership.client)
        membership.refresh_from_db()
        today = timezone.localdate()
        client = membership.client

        if membership.status != MembershipStatus.ACTIVE:
            raise serializers.ValidationError('Абонемент не активен')

        if membership.visits_remaining <= 0:
            raise serializers.ValidationError('Посещения закончились')

        if Visit.objects.filter(
            membership__client=client, 
            marked_at__date=today,
            cancelled_at__isnull=True,
            ).exists():
            raise serializers.ValidationError('Вы уже отмечали этого клиента сегодня')

        return attrs

    def create(self, validated_data):
        membership = self.context['membership']
        request = self.context['request']

        with transaction.atomic():
            visit = Visit.objects.create(
                membership=membership,
                marked_by=request.user,
                notes=validated_data.get('notes', '')
            )
            membership.visits_remaining -= 1
            if membership.visits_remaining == 0:
                membership.status = MembershipStatus.DEPLETED
            membership.save(update_fields=['status', 'visits_remaining'])
        return visit


class MembershipCancelSerializer(serializers.Serializer):
    reason = serializers.CharField(required=True)

    def validate(self, attrs):
        membership = self.instance
        Membership.sync_overdue(client=membership.client)
        membership.refresh_from_db()
        time_now = timezone.now()
        employee = self.context['request'].user

        if membership.status != MembershipStatus.ACTIVE:
            raise serializers.ValidationError('Этот абонемент неактивен')

        if membership.visits_remaining < membership.visits_total:
            raise serializers.ValidationError('Невозможно отменить не полный абонемент')

        if (time_now - membership.issued_at) > timedelta(hours=24) and employee.role == User.Role.TRAINER:
            raise serializers.ValidationError('Прошло более 24 часов с момента выдачи абонемента. Обратитесь к администратору')

        return attrs

    def update(self, instance, validated_data):
        instance.status = MembershipStatus.CANCELLED
        instance.cancel_reason = validated_data.get('reason', '')
        instance.cancelled_at = timezone.now()
        instance.cancelled_by = self.context['request'].user

        instance.save()
        return instance


class VisitCancelSerializer(serializers.Serializer):
    reason = serializers.CharField(required=True)

    def validate(self, attrs):
        visit = self.instance
        time_now = timezone.now()
        employee = self.context['request'].user
        membership = visit.membership
        Membership.sync_overdue(client=membership.client)
        membership.refresh_from_db()

        if visit.cancelled_at is not None:
            raise serializers.ValidationError('Это посещение уже отменено')
        
        if membership.status == MembershipStatus.CANCELLED or membership.status == MembershipStatus.EXPIRED:
            raise serializers.ValidationError('Этот абонемент не активен')

        if (time_now - visit.marked_at) > timedelta(hours=24) and employee.role == User.Role.TRAINER:
            raise serializers.ValidationError('Прошло более 24 часов с момента отметки посещения. Обратитесь к администратору')

        if membership.visits_remaining == membership.visits_total:
            raise serializers.ValidationError('Абонемент полный')

        return attrs

    def update(self, instance, validated_data):
        instance.cancel_reason = validated_data.get('reason', '')
        instance.cancelled_at = timezone.now()
        instance.cancelled_by = self.context['request'].user
        membership = instance.membership

        with transaction.atomic():
            membership.visits_remaining += 1
            if membership.status == MembershipStatus.DEPLETED:
                membership.status = MembershipStatus.ACTIVE
            membership.save(update_fields=['status', 'visits_remaining'])
            instance.save()

        return instance


class PaymentCreateSerializer(serializers.Serializer):
    amount = serializers.IntegerField(required=True)
    comment = serializers.CharField(required=False, allow_blank=True, default='')
    paid_at = serializers.DateField()
    transaction_id = serializers.CharField(required=True, max_length=255)
    payer_name = serializers.CharField(required=True)

    def create(self, validated_data):
        return Payment.objects.create(
            amount=validated_data['amount'],
            membership=self.context['membership'],
            paid_at=validated_data['paid_at'],
            transaction_id=validated_data['transaction_id'],
            payer_name=validated_data['payer_name'],
            comment=validated_data.get('comment', ''),
        )

    def update(self, instance, validated_data):
        instance.amount = validated_data['amount']
        instance.paid_at = validated_data['paid_at']
        instance.transaction_id = validated_data['transaction_id']
        instance.payer_name = validated_data['payer_name']
        instance.comment = validated_data.get('comment', '')
        instance.save()
        return instance
