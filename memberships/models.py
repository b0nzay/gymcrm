from django.db import models
from django.db.models import UniqueConstraint, Q
from datetime import date
from users.models import User

class MembershipPlan(models.Model):
    name = models.CharField(max_length=255)
    visits_total = models.PositiveSmallIntegerField()
    validity_days = models.PositiveSmallIntegerField()
    price_list = models.IntegerField()
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} - {self.visits_total} посещений, цена: {self.price_list} руб."


class MembershipStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    DEPLETED = 'depleted', 'Depleted'
    EXPIRED = 'expired', 'Expired'
    CANCELLED = 'cancelled', 'Cancelled'

class Membership(models.Model):
    client = models.ForeignKey(User, related_name='membership_client', limit_choices_to={'role': User.Role.CLIENT}, on_delete=models.CASCADE)
    plan = models.ForeignKey(MembershipPlan, on_delete=models.PROTECT)
    issued_by = models.ForeignKey(User, related_name='membership_issued', limit_choices_to={'role__in': [User.Role.TRAINER, User.Role.ADMIN]}, on_delete=models.SET_NULL, null=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateField()
    visits_total = models.PositiveSmallIntegerField()
    visits_remaining = models.PositiveSmallIntegerField()
    price_list = models.IntegerField()
    price_paid = models.IntegerField()
    status = models.CharField(max_length=20, choices=MembershipStatus.choices, default=MembershipStatus.ACTIVE)
    notes = models.TextField(blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(User, related_name='membership_cancelled', limit_choices_to={'role__in': [User.Role.TRAINER, User.Role.ADMIN]}, on_delete=models.SET_NULL, null=True, blank=True)
    cancel_reason = models.TextField(blank=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['client'],
                condition=Q(status=MembershipStatus.ACTIVE),
                name='one_active_membership_per_client'
            )
        ]

    def __str__(self):
        return f"{self.client.first_name} {self.client.last_name} - {self.plan.name} - {self.issued_at} - {self.valid_until}"

class Visit(models.Model):
    membership = models.ForeignKey(Membership, on_delete=models.CASCADE)
    marked_by = models.ForeignKey(User, related_name='visit_marked', limit_choices_to={'role__in': [User.Role.TRAINER, User.Role.ADMIN]}, on_delete=models.SET_NULL, null=True)
    marked_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(User, related_name='visit_cancelled', limit_choices_to={'role__in': [User.Role.TRAINER, User.Role.ADMIN]}, on_delete=models.SET_NULL, null=True, blank=True)
    cancel_reason = models.TextField(blank=True)

    def __str__(self):
        return f"{self.membership.client.first_name} {self.membership.client.last_name} - {self.membership.plan.name} - {self.marked_at}"


class Payment(models.Model):
    membership = models.ForeignKey(Membership, on_delete=models.CASCADE)
    amount = models.IntegerField()
    paid_at = models.DateField()
    transaction_id = models.CharField(max_length=255)
    payer_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(blank=True)

    def __str__(self):
        return f"{self.payer_name} оплатил {self.amount} {self.paid_at} числа по абонементу {self.membership}"
