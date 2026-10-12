from rest_framework.test import APIClient

from users.models import User
from memberships.models import Membership, MembershipPlan, MembershipStatus


def make_user(username, password='Pass12345', role=User.Role.CLIENT, **extra):
    extra.setdefault('first_name', 'Имя')
    extra.setdefault('last_name', 'Фамилия')
    return User.objects.create_user(username=username, password=password, role=role, **extra)


def make_plan(**extra):
    extra.setdefault('name', 'Месяц')
    extra.setdefault('visits_total', 8)
    extra.setdefault('validity_days', 30)
    extra.setdefault('price_list', 3000)
    extra.setdefault('is_active', True)
    return MembershipPlan.objects.create(**extra)


def issue_membership(client, plan, issued_by):
    from datetime import timedelta
    from django.utils import timezone

    return Membership.objects.create(
        client=client,
        plan=plan,
        issued_by=issued_by,
        valid_until=timezone.localdate() + timedelta(days=plan.validity_days),
        visits_total=plan.visits_total,
        visits_remaining=plan.visits_total,
        price_list=plan.price_list,
        status=MembershipStatus.ACTIVE,
    )


def auth_client(user):
    api = APIClient()
    api.force_authenticate(user=user)
    return api
