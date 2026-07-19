from rest_framework import serializers

from .models import MembershipPlan, Membership, Visit, MembershipStatus
from users.models import User

from datetime import date, timedelta

from django.db import transaction

class MembershipPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipPlan
        fields = ['id','name', 'visits_total', 'validity_days', 'price_list', 'notes']

class MembershipPlanCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipPlan
        fields = ['name', 'visits_total', 'validity_days', 'price_list', 'sort_order', 'notes']

class MembershipSerializer(serializers.ModelSerializer):
    plan = MembershipPlanSerializer(read_only=True)

    class Meta:
        model = Membership
        fields = ['id', 'client', 'plan', 'issued_by', 'issued_at', 'valid_until', 'visits_total', 'visits_remaining', 'price_list', 'price_paid', 'status', 'notes']
        read_only_fields = fields

class MembershipCreateSerializer(serializers.Serializer):
    client_id = serializers.IntegerField()
    plan_id = serializers.IntegerField()
    price_paid = serializers.IntegerField(required=False)
    issued_at = serializers.DateField(required=False)
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
        if Membership.objects.filter(client=client, status=MembershipStatus.ACTIVE).exists():
            raise serializers.ValidationError('У клиента уже есть активный абонемент')
        return attrs

    def create(self, validated_data):
        client = User.objects.get(pk=validated_data['client_id'])
        plan = MembershipPlan.objects.get(pk=validated_data['plan_id'])
        issued_at = validated_data.get('issued_at', date.today())
        price_paid = validated_data.get('price_paid', plan.price_list)
        request = self.context['request']

        return Membership.objects.create(
            client=client,
            plan=plan,
            issued_by=request.user,
            issued_at=issued_at,
            valid_until=issued_at + timedelta(days=plan.validity_days),
            visits_total=plan.visits_total,
            visits_remaining=plan.visits_total,
            price_list=plan.price_list,
            price_paid=price_paid,
            status=MembershipStatus.ACTIVE,
            notes=validated_data.get('notes', ''))


class VisitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visit
        fields = ['id', 'membership', 'marked_by', 'marked_at', 'notes']
        read_only_fields = fields

class VisitCreateSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, allow_blank=True, default='')
    
    def validate(self, attrs):
        membership = self.context['membership']
        today = date.today()
        client = membership.client

        if membership.status != MembershipStatus.ACTIVE:
            raise serializers.ValidationError('Абонемент не активен')

        if today > membership.valid_until:
            membership.status = MembershipStatus.EXPIRED
            membership.save(update_fields=['status'])
            raise serializers.ValidationError('Срок абонемента истёк')

        if membership.visits_remaining <= 0:
            raise serializers.ValidationError('Посещения закончились')

        if Visit.objects.filter(
            membership__client=client, 
            marked_at__date=today
            ).exists():
            raise serializers.ValidationError('Вы уже посетили занятие сегодня')

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