from rest_framework import status
from rest_framework.test import APITestCase

from users.models import AccessCode, User
from users.test_utils import auth_client, make_user


class AuthApiTests(APITestCase):
    def setUp(self):
        AccessCode.objects.create(code='ABCD2345', is_active=True)
        self.password = 'Pass12345'
        self.user = make_user('ivanov', password=self.password)

    def test_login_is_case_insensitive(self):
        for username in ('ivanov', 'Ivanov', 'IVANOV'):
            response = self.client.post(
                '/api/auth/login/',
                {'username': username, 'password': self.password},
                format='json',
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK, username)
            self.assertIn('access', response.data)

    def test_login_rejects_wrong_password(self):
        response = self.client.post(
            '/api/auth/login/',
            {'username': 'ivanov', 'password': 'wrong'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_with_valid_code(self):
        response = self.client.post(
            '/api/auth/register/',
            {
                'username': 'petrov',
                'password': self.password,
                'access_code': 'ABCD2345',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = User.objects.get(username='petrov')
        self.assertEqual(created.role, User.Role.CLIENT)

    def test_register_rejects_bad_code_and_duplicate_username(self):
        bad = self.client.post(
            '/api/auth/register/',
            {
                'username': 'sidorov',
                'password': self.password,
                'access_code': 'WRONG',
            },
            format='json',
        )
        self.assertEqual(bad.status_code, status.HTTP_400_BAD_REQUEST)

        duplicate = self.client.post(
            '/api/auth/register/',
            {
                'username': 'Ivanov',
                'password': self.password,
                'access_code': 'ABCD2345',
            },
            format='json',
        )
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)


class PermissionApiTests(APITestCase):
    def setUp(self):
        self.client_user = make_user('client1', role=User.Role.CLIENT)
        self.trainer = make_user('trainer1', role=User.Role.TRAINER)
        self.admin = make_user('admin1', role=User.Role.ADMIN)

    def test_client_cannot_list_clients_or_stats(self):
        api = auth_client(self.client_user)
        self.assertEqual(api.get('/api/clients/').status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(api.get('/api/stats/').status_code, status.HTTP_403_FORBIDDEN)

    def test_trainer_can_list_clients_but_not_rotate_code(self):
        api = auth_client(self.trainer)
        self.assertEqual(api.get('/api/clients/').status_code, status.HTTP_200_OK)
        self.assertEqual(api.get('/api/auth/access-code/').status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(api.post('/api/auth/access-code/rotate/').status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_read_access_code(self):
        AccessCode.objects.create(code='XY34KLMN', is_active=True)
        api = auth_client(self.admin)
        response = api.get('/api/auth/access-code/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 'XY34KLMN')

    def test_anonymous_cannot_hit_me(self):
        self.assertEqual(self.client.get('/api/auth/me/').status_code, status.HTTP_401_UNAUTHORIZED)
