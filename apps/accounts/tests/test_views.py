# =============================================================
# MonTour — apps/accounts/tests/test_views.py
# Tests unitaires et d'intégration — Authentification
# =============================================================

import re
from datetime import timedelta

from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from apps.accounts.models import User, EmailVerificationToken, PasswordResetToken


class AuthTests(APITestCase):
    """Tests pour les endpoints d'authentification."""

    def setUp(self):
        cache.clear()  # remet à zéro les compteurs de throttle entre les tests
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
        # Aucun JWT tant que l'email n'est pas confirmé
        self.assertNotIn('access',  resp.data['data'])
        self.assertNotIn('refresh', resp.data['data'])
        self.assertFalse(resp.data['data']['email_verified'])
        self.assertEqual(User.objects.count(), 1)
        self.assertFalse(User.objects.get().email_verified)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['moussa@test.bj'])

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
            email='moussa@test.bj', username='Moussa', password='TestPass123!',
            email_verified=True,
        )
        resp = self.client.post(self.login_url, {'email': 'moussa@test.bj', 'password': 'TestPass123!'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', resp.data['data'])

    def test_login_refused_until_email_verified(self):
        User.objects.create_user(email='moussa@test.bj', username='Moussa', password='TestPass123!')
        resp = self.client.post(self.login_url, {'email': 'moussa@test.bj', 'password': 'TestPass123!'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(resp.data['error']['details']['email_not_verified'])
        self.assertNotIn('access', str(resp.data))

    def test_login_wrong_password_does_not_reveal_unverified(self):
        User.objects.create_user(email='moussa@test.bj', username='Moussa', password='Correct123!')
        resp = self.client.post(self.login_url, {'email': 'moussa@test.bj', 'password': 'Wrong123!'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

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


class EmailVerificationTests(APITestCase):
    """Flux complet : inscription, email, vérification, connexion."""

    register_url = '/api/v1/auth/register/'
    login_url    = '/api/v1/auth/login/'
    verify_url   = '/api/v1/auth/verify-email/'
    resend_url   = '/api/v1/auth/resend-verification/'

    def setUp(self):
        cache.clear()
        self.creds = {'email': 'moussa@test.bj', 'password': 'TestPass123!'}
        self.client.post(self.register_url, {
            'username': 'Moussa Test', 'phone': '+22961000000', 'priority': 'normal',
            'password2': self.creds['password'], **self.creds,
        }, format='json')
        self.user = User.objects.get(email=self.creds['email'])

    def _token_from_mail(self, message):
        return re.search(r'verify_email=([\w\-]+)', message.body).group(1)

    def test_email_links_to_web_app_not_api(self):
        body = mail.outbox[0].body
        self.assertIn('/?verify_email=', body)
        self.assertNotIn('/api/', body)

    def test_full_flow(self):
        token = self._token_from_mail(mail.outbox[0])
        resp = self.client.post(self.verify_url, {'token': token}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', resp.data['data'])
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)

        resp = self.client.post(self.login_url, self.creds, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_verify_requires_post(self):
        token = self._token_from_mail(mail.outbox[0])
        resp = self.client.get(self.verify_url, {'token': token})
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.user.refresh_from_db()
        self.assertFalse(self.user.email_verified)

    def test_token_is_single_use(self):
        token = self._token_from_mail(mail.outbox[0])
        self.client.post(self.verify_url, {'token': token}, format='json')
        resp = self.client.post(self.verify_url, {'token': token}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_and_missing_token(self):
        self.assertEqual(self.client.post(self.verify_url, {'token': 'nope'}, format='json').status_code, 400)
        self.assertEqual(self.client.post(self.verify_url, {}, format='json').status_code, 400)

    def test_expired_token(self):
        token = self._token_from_mail(mail.outbox[0])
        EmailVerificationToken.objects.update(expires_at=timezone.now() - timedelta(minutes=1))
        resp = self.client.post(self.verify_url, {'token': token}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertFalse(self.user.email_verified)

    def test_resend_invalidates_previous_token(self):
        old = self._token_from_mail(mail.outbox[0])
        resp = self.client.post(self.resend_url, {'email': self.creds['email']}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 2)
        new = self._token_from_mail(mail.outbox[1])
        self.assertNotEqual(old, new)
        self.assertEqual(self.client.post(self.verify_url, {'token': old}, format='json').status_code, 400)
        self.assertEqual(self.client.post(self.verify_url, {'token': new}, format='json').status_code, 200)

    def test_resend_is_generic_for_unknown_and_verified(self):
        unknown = self.client.post(self.resend_url, {'email': 'ghost@test.bj'}, format='json')
        self.user.email_verified = True
        self.user.save()
        verified = self.client.post(self.resend_url, {'email': self.creds['email']}, format='json')
        self.assertEqual(unknown.status_code, verified.status_code)
        self.assertEqual(unknown.data['message'], verified.data['message'])
        self.assertEqual(len(mail.outbox), 1)  # aucun envoi supplémentaire


class PasswordResetTests(APITestCase):
    """Mot de passe oublié : email, lien vers l'app web, nouveau mot de passe."""

    forgot_url = '/api/v1/auth/forgot-password/'
    reset_url  = '/api/v1/auth/reset-password/'
    login_url  = '/api/v1/auth/login/'

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            email='moussa@test.bj', username='Moussa', password='OldPass123!', email_verified=True,
        )

    def _request_reset(self):
        self.client.post(self.forgot_url, {'email': 'moussa@test.bj'}, format='json')
        return re.search(r'reset_password=([\w\-]+)', mail.outbox[-1].body).group(1)

    def test_link_points_to_web_app(self):
        self._request_reset()
        body = mail.outbox[-1].body
        self.assertIn('/?reset_password=', body)
        self.assertNotIn('montour.bj/reset-password', body)

    def test_full_flow(self):
        token = self._request_reset()
        resp = self.client.post(self.reset_url, {
            'token': token, 'password': 'NewPass456!', 'password2': 'NewPass456!',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        ok = self.client.post(self.login_url, {'email': 'moussa@test.bj', 'password': 'NewPass456!'}, format='json')
        self.assertEqual(ok.status_code, status.HTTP_200_OK)
        old = self.client.post(self.login_url, {'email': 'moussa@test.bj', 'password': 'OldPass123!'}, format='json')
        self.assertEqual(old.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_is_single_use(self):
        token = self._request_reset()
        data = {'token': token, 'password': 'NewPass456!', 'password2': 'NewPass456!'}
        self.client.post(self.reset_url, data, format='json')
        again = self.client.post(self.reset_url, {**data, 'password': 'Other789!x', 'password2': 'Other789!x'}, format='json')
        self.assertEqual(again.status_code, status.HTTP_400_BAD_REQUEST)

    def test_new_request_invalidates_previous_link(self):
        old = self._request_reset()
        new = self._request_reset()
        self.assertNotEqual(old, new)
        data = {'password': 'NewPass456!', 'password2': 'NewPass456!'}
        self.assertEqual(self.client.post(self.reset_url, {'token': old, **data}, format='json').status_code, 400)
        self.assertEqual(self.client.post(self.reset_url, {'token': new, **data}, format='json').status_code, 200)

    def test_weak_or_mismatched_password_rejected(self):
        token = self._request_reset()
        weak = self.client.post(self.reset_url, {'token': token, 'password': 'password', 'password2': 'password'}, format='json')
        self.assertEqual(weak.status_code, status.HTTP_400_BAD_REQUEST)
        mismatch = self.client.post(self.reset_url, {'token': token, 'password': 'NewPass456!', 'password2': 'Different1!'}, format='json')
        self.assertEqual(mismatch.status_code, status.HTTP_400_BAD_REQUEST)
        # le token n'est pas consommé par une tentative invalide
        ok = self.client.post(self.reset_url, {'token': token, 'password': 'NewPass456!', 'password2': 'NewPass456!'}, format='json')
        self.assertEqual(ok.status_code, status.HTTP_200_OK)

    def test_expired_token(self):
        token = self._request_reset()
        PasswordResetToken.objects.update(expires_at=timezone.now() - timedelta(minutes=1))
        resp = self.client.post(self.reset_url, {'token': token, 'password': 'NewPass456!', 'password2': 'NewPass456!'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_also_confirms_email(self):
        self.user.email_verified = False
        self.user.save()
        token = self._request_reset()
        self.client.post(self.reset_url, {'token': token, 'password': 'NewPass456!', 'password2': 'NewPass456!'}, format='json')
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)

    def test_forgot_is_generic_for_unknown_email(self):
        known = self.client.post(self.forgot_url, {'email': 'moussa@test.bj'}, format='json')
        unknown = self.client.post(self.forgot_url, {'email': 'ghost@test.bj'}, format='json')
        self.assertEqual(known.data['message'], unknown.data['message'])
        self.assertEqual(len(mail.outbox), 1)


class EmailLinkSecurityTests(APITestCase):
    """Les liens des emails ne doivent jamais dépendre de l'en-tête Host."""

    data = {
        'username': 'Moussa Test', 'email': 'moussa@test.bj', 'phone': '+22961000000',
        'password': 'TestPass123!', 'password2': 'TestPass123!', 'priority': 'normal',
    }

    def setUp(self):
        cache.clear()

    @override_settings(ALLOWED_HOSTS=['*'], FRONTEND_URL='https://montour.example')
    def test_forged_host_header_cannot_redirect_links(self):
        self.client.post('/api/v1/auth/register/', self.data, format='json', HTTP_HOST='evil.com')
        User.objects.update(email_verified=True)
        self.client.post('/api/v1/auth/forgot-password/', {'email': 'moussa@test.bj'}, format='json', HTTP_HOST='evil.com')
        for message in mail.outbox:
            self.assertIn('https://montour.example/?', message.body)
            self.assertNotIn('evil.com', message.body)

    @override_settings(
        DEBUG=False, EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend',
    )
    def test_register_reports_unsent_email_when_smtp_missing(self):
        resp = self.client.post('/api/v1/auth/register/', self.data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertFalse(resp.data['data']['email_sent'])


class SmtpFailureTests(APITestCase):
    """Un SMTP qui refuse les identifiants ne doit ni faire planter l'inscription ni passer inaperçu."""

    def setUp(self):
        cache.clear()

    def test_register_survives_smtp_auth_error_and_reports_it(self):
        import smtplib
        from unittest import mock
        err = smtplib.SMTPAuthenticationError(535, b'5.7.8 Username and Password not accepted')
        with mock.patch('apps.accounts.emails.send_mail', side_effect=err), \
                self.assertLogs('apps', level='ERROR') as logs:
            resp = self.client.post('/api/v1/auth/register/', {
                'username': 'Moussa Test', 'email': 'moussa@test.bj', 'phone': '+22961000000',
                'password': 'TestPass123!', 'password2': 'TestPass123!', 'priority': 'normal',
            }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertFalse(resp.data['data']['email_sent'])
        self.assertTrue(any("mot de passe d'application" in m for m in logs.output))
        self.assertTrue(User.objects.filter(email='moussa@test.bj').exists())


class HealthTests(APITestCase):
    def test_health_reports_persistent_storage(self):
        resp = self.client.get('/api/health/')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()['persistent_storage'])

    @override_settings(IS_VERCEL=True)
    def test_health_degraded_on_vercel_sqlite(self):
        data = self.client.get('/api/health/').json()
        self.assertFalse(data['persistent_storage'])
        self.assertEqual(data['status'], 'degraded')


class ThrottleScopeTests(APITestCase):
    """Inscription, connexion et renvoi ont chacun leur propre limite."""

    def test_register_does_not_consume_login_budget(self):
        cache.clear()
        for i in range(5):  # épuise la limite d'inscription (5/min)
            self.client.post('/api/v1/auth/register/', {'email': f'bad{i}'}, format='json')
        self.assertEqual(self.client.post('/api/v1/auth/register/', {}, format='json').status_code, 429)
        login = self.client.post('/api/v1/auth/login/', {'email': 'a@b.bj', 'password': 'x'}, format='json')
        self.assertEqual(login.status_code, status.HTTP_401_UNAUTHORIZED)
        resend = self.client.post('/api/v1/auth/resend-verification/', {'email': 'a@b.bj'}, format='json')
        self.assertEqual(resend.status_code, status.HTTP_200_OK)


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
        self.assertTrue(user.email_verified)

    def test_new_user_is_unverified_by_default(self):
        user = User.objects.create_user(email='new@bj', username='New', password='pass')
        self.assertFalse(user.email_verified)

    def test_is_admin_property(self):
        user = User(role=User.ROLE_ADMIN)
        self.assertTrue(user.is_admin)

    def test_priority_score_base(self):
        user = User(priority=User.PRIORITY_URGENT)
        self.assertEqual(user.priority_score_base, 100)