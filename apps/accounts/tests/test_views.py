# =============================================================
# MonTour — apps/accounts/tests/test_views.py
# Tests unitaires et d'intégration — Authentification
# =============================================================

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from apps.accounts.models import User


class AuthTests(APITestCase):
    """Tests pour les endpoints d'authentification."""

    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/v1/auth/register/'
        self.login_url    = '/api/v1/auth/login/'
        self.me_url       = '/api/v1/auth/me/'

        # Utilisateur de test
        self.user_data = {
            'username': 'Moussa Test',
            'email':    'moussa@test.bj',
            'phone':    '+22961000000',
            'password':  'TestPass123!',
            'password2': 'TestPass123!',
            'priority':  'normal',
        }

    # ── Inscription ───────────────────────────────────────────
    def test_register_success(self):
        resp = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn('access',  resp.data['data'])
        self.assertIn('refresh', resp.data['data'])
        self.assertIn('user',    resp.data['data'])
        self.assertEqual(User.objects.count(), 1)

    def test_register_duplicate_email(self):
        self.client.post(self.register_url, self.user_data, format='json')
        resp = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_password_mismatch(self):
        data = {**self.user_data, 'password2': 'WrongPass!'}
        resp = self.client.post(self.register_url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_email(self):
        data = {k: v for k, v in self.user_data.items() if k != 'email'}
        resp = self.client.post(self.register_url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    # ── Connexion ─────────────────────────────────────────────
    def test_login_success(self):
        User.objects.create_user(
            email='moussa@test.bj', username='Moussa', password='TestPass123!'
        )
        resp = self.client.post(self.login_url, {'email': 'moussa@test.bj', 'password': 'TestPass123!'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', resp.data['data'])

    def test_login_wrong_password(self):
        User.objects.create_user(email='moussa@test.bj', username='Moussa', password='Correct!')
        resp = self.client.post(self.login_url, {'email': 'moussa@test.bj', 'password': 'Wrong!'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_unknown_email(self):
        resp = self.client.post(self.login_url, {'email': 'unknown@test.bj', 'password': 'Pass123!'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    # ── Profil ────────────────────────────────────────────────
    def test_get_me_authenticated(self):
        user = User.objects.create_user(email='me@test.bj', username='Me', password='Pass123!')
        self.client.force_authenticate(user=user)
        resp = self.client.get(self.me_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['data']['email'], 'me@test.bj')

    def test_get_me_unauthenticated(self):
        resp = self.client.get(self.me_url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_profile(self):
        user = User.objects.create_user(email='update@test.bj', username='Old', password='Pass123!')
        self.client.force_authenticate(user=user)
        resp = self.client.put(self.me_url, {'username': 'New Name', 'priority': 'senior'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['data']['username'], 'New Name')


class UserModelTests(TestCase):
    """Tests sur le modèle User."""

    def test_create_user(self):
        user = User.objects.create_user(email='test@bj', username='Test', password='pass')
        self.assertEqual(user.email, 'test@bj')
        self.assertEqual(user.role, User.ROLE_USER)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)

    def test_create_superuser(self):
        user = User.objects.create_superuser(email='admin@bj', password='admin')
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertEqual(user.role, User.ROLE_ADMIN)

    def test_is_admin_property(self):
        user = User(role=User.ROLE_ADMIN)
        self.assertTrue(user.is_admin)

    def test_priority_score_base(self):
        user = User(priority=User.PRIORITY_URGENT)
        self.assertEqual(user.priority_score_base, 100)