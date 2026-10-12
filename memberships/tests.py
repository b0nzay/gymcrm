from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from memberships.models import Membership, MembershipStatus, Visit
from users.models import User
from users.test_utils import auth_client, issue_membership, make_plan, make_user


class MembershipApiTests(APITestCase):
    def setUp(self):
        self.client_user = make_user('client11', role=User.Role.CLIENT)
        self.other = make_user('client12', role=User.Role.CLIENT)
        self.trainer = make_user('trainer13', role=User.Role.TRAINER)
        self.admin = make_user('admin14', role=User.Role.ADMIN)
        self.plan = make_plan()

    def test_client_cannot_issue_membership(self):
        api = auth_client(self.client_user)
        response = api.post(
            '/api/memberships/',
            {'client_id': self.client_user.id, 'plan_id': self.plan.id},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_trainer_issues_and_second_active_is_rejected(self):
        api = auth_client(self.trainer)
        first = api.post(
            '/api/memberships/',
            {'client_id': self.client_user.id, 'plan_id': self.plan.id},
            format='json',
        )
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(first.data['status'], MembershipStatus.ACTIVE)

        second = api.post(
            '/api/memberships/',
            {'client_id': self.client_user.id, 'plan_id': self.plan.id},
            format='json',
        )
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_issue_inactive_plan(self):
        self.plan.is_active = False
        self.plan.save(update_fields=['is_active'])
        api = auth_client(self.trainer)
        response = api.post(
            '/api/memberships/',
            {'client_id': self.client_user.id, 'plan_id': self.plan.id},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_overdue_active_becomes_expired_on_current(self):
        membership = issue_membership(self.client_user, self.plan, self.trainer)
        membership.valid_until = timezone.localdate() - timedelta(days=1)
        membership.save(update_fields=['valid_until'])

        api = auth_client(self.client_user)
        response = api.get('/api/memberships/current/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        membership.refresh_from_db()
        self.assertEqual(membership.status, MembershipStatus.EXPIRED)

    def test_zero_visits_becomes_depleted_on_sync(self):
        membership = issue_membership(self.client_user, self.plan, self.trainer)
        membership.visits_remaining = 0
        membership.save(update_fields=['visits_remaining'])

        api = auth_client(self.client_user)
        api.get('/api/memberships/current/')
        membership.refresh_from_db()
        self.assertEqual(membership.status, MembershipStatus.DEPLETED)

    def test_cancel_full_membership(self):
        membership = issue_membership(self.client_user, self.plan, self.trainer)
        api = auth_client(self.trainer)
        response = api.post(
            f'/api/memberships/{membership.id}/cancel/',
            {'reason': 'ошибка выдачи'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        membership.refresh_from_db()
        self.assertEqual(membership.status, MembershipStatus.CANCELLED)

    def test_cannot_cancel_after_visit(self):
        membership = issue_membership(self.client_user, self.plan, self.trainer)
        api = auth_client(self.trainer)
        api.post(f'/api/memberships/{membership.id}/visits/', {'notes': ''}, format='json')
        response = api.post(
            f'/api/memberships/{membership.id}/cancel/',
            {'reason': 'поздно'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_trainer_cannot_cancel_after_24h_admin_can(self):
        membership = issue_membership(self.client_user, self.plan, self.trainer)
        Membership.objects.filter(pk=membership.pk).update(
            issued_at=timezone.now() - timedelta(hours=25),
        )
        trainer_api = auth_client(self.trainer)
        blocked = trainer_api.post(
            f'/api/memberships/{membership.id}/cancel/',
            {'reason': 'ошибка'},
            format='json',
        )
        self.assertEqual(blocked.status_code, status.HTTP_400_BAD_REQUEST)

        admin_api = auth_client(self.admin)
        allowed = admin_api.post(
            f'/api/memberships/{membership.id}/cancel/',
            {'reason': 'ошибка выдачи'},
            format='json',
        )
        self.assertEqual(allowed.status_code, status.HTTP_200_OK)
        membership.refresh_from_db()
        self.assertEqual(membership.status, MembershipStatus.CANCELLED)


class VisitApiTests(APITestCase):
    def setUp(self):
        self.client_user = make_user('client21', role=User.Role.CLIENT)
        self.trainer = make_user('trainer22', role=User.Role.TRAINER)
        self.plan = make_plan(visits_total=2, validity_days=30)
        self.membership = issue_membership(self.client_user, self.plan, self.trainer)

    def test_client_cannot_mark_visit(self):
        api = auth_client(self.client_user)
        response = api.post(
            f'/api/memberships/{self.membership.id}/visits/',
            {'notes': ''},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_trainer_marks_visit_and_second_same_day_fails(self):
        api = auth_client(self.trainer)
        first = api.post(
            f'/api/memberships/{self.membership.id}/visits/',
            {'notes': 'ок'},
            format='json',
        )
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.membership.refresh_from_db()
        self.assertEqual(self.membership.visits_remaining, 1)

        second = api.post(
            f'/api/memberships/{self.membership.id}/visits/',
            {'notes': ''},
            format='json',
        )
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_mark_on_expired_or_cancelled(self):
        api = auth_client(self.trainer)
        self.membership.status = MembershipStatus.CANCELLED
        self.membership.save(update_fields=['status'])
        cancelled = api.post(
            f'/api/memberships/{self.membership.id}/visits/',
            {'notes': ''},
            format='json',
        )
        self.assertEqual(cancelled.status_code, status.HTTP_400_BAD_REQUEST)

        other = make_user('client23', role=User.Role.CLIENT)
        expired = issue_membership(other, self.plan, self.trainer)
        expired.valid_until = timezone.localdate() - timedelta(days=1)
        expired.save(update_fields=['valid_until'])
        response = api.post(
            f'/api/memberships/{expired.id}/visits/',
            {'notes': ''},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expired.refresh_from_db()
        self.assertEqual(expired.status, MembershipStatus.EXPIRED)

    def test_last_visit_depletes_and_blocks_next(self):
        small = make_plan(name='Разовое', visits_total=1, validity_days=10, price_list=500)
        client = make_user('client24', role=User.Role.CLIENT)
        membership = issue_membership(client, small, self.trainer)
        api = auth_client(self.trainer)
        first = api.post(f'/api/memberships/{membership.id}/visits/', {'notes': ''}, format='json')
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        membership.refresh_from_db()
        self.assertEqual(membership.status, MembershipStatus.DEPLETED)

        again = api.post(f'/api/memberships/{membership.id}/visits/', {'notes': ''}, format='json')
        self.assertEqual(again.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_can_cancel_visit(self):
        api = auth_client(self.trainer)
        created = api.post(
            f'/api/memberships/{self.membership.id}/visits/',
            {'notes': ''},
            format='json',
        )
        visit_id = created.data['id']
        admin_api = auth_client(make_user('admin25', role=User.Role.ADMIN))
        response = admin_api.post(
            f'/api/memberships/visits/{visit_id}/cancel/',
            {'reason': 'ошибка'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        visit = Visit.objects.get(pk=visit_id)
        self.assertIsNotNone(visit.cancelled_at)
        self.membership.refresh_from_db()
        self.assertEqual(self.membership.visits_remaining, self.membership.visits_total)
