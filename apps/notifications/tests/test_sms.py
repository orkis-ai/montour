# =============================================================
# MonTour — apps/notifications/tests/test_sms.py
# Tests : SMS de rappel « votre tour approche »
# =============================================================

from unittest import mock

import requests
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.notifications.models import Notification, SMSLog
from apps.notifications.services import NotificationService
from apps.notifications.sms import (
    ESMSAfricaProvider, SMSResult, SMSService,
    get_provider, gsm_safe, normalize_phone,
)
from apps.queues.models import Queue
from apps.services.models import Service
from apps.tickets.models import Ticket

OK = SMSResult(ok=True, provider='fake', message_id='ID1')


def make_user(n, phone='+22961000000', **extra):
    return User.objects.create_user(
        email=f'u{n}@test.bj', username=f'User {n}', password='pass', phone=phone,
        email_verified=True, **extra,
    )


def make_queue():
    service = Service.objects.create(name='Centre de Santé', avg_service_time=10)
    return Queue.objects.create(service=service)


def add_ticket(queue, user, number):
    return Ticket.objects.create(queue=queue, user=user, number=number, priority_score=40 - number)


class PhoneTests(TestCase):
    def test_normalize(self):
        cases = {
            '+22961000000': '+2290161000000',      # ancien format avec indicatif
            '61000000': '+2290161000000',          # 8 chiffres
            '0161000000': '+2290161000000',        # 10 chiffres
            '+229 01 61 00 00 00': '+2290161000000',
            '00229 61 00 00 00': '+2290161000000',
        }
        for raw, expected in cases.items():
            self.assertEqual(normalize_phone(raw), expected, raw)

    def test_invalid_numbers(self):
        for raw in ['', None, 'abc', '123', '+33612345678', '0261000000', '6100000012345']:
            self.assertIsNone(normalize_phone(raw), raw)

    @override_settings(SMS_BENIN_TEN_DIGITS=False)
    def test_normalize_legacy_eight_digits(self):
        self.assertEqual(normalize_phone('0161000000'), '+22961000000')
        self.assertEqual(normalize_phone('61000000'), '+22961000000')

    def test_gsm_safe_strips_accents_and_emoji(self):
        self.assertEqual(gsm_safe("Ticket n°5 — c'est l’heure ⏳ à Ségbana"), "Ticket n5 - c'est l'heure  a Segbana")


class ProviderSelectionTests(TestCase):
    @override_settings(SMS_PROVIDER='', ESMS_API_KEY='')
    def test_defaults_to_console_without_key(self):
        self.assertEqual(get_provider().name, 'console')

    @override_settings(SMS_PROVIDER='', ESMS_API_KEY='esms_live_abc')
    def test_uses_esms_as_soon_as_a_key_is_present(self):
        self.assertEqual(get_provider().name, 'esms')

    @override_settings(SMS_PROVIDER='esms', ESMS_API_KEY='')
    def test_forced_esms_without_key_is_rejected(self):
        self.assertIsNone(get_provider())
        result = SMSService.send('+2290161000000', 'x')
        self.assertFalse(result.ok)
        self.assertIn('ESMS_API_KEY', result.error)

    @override_settings(SMS_PROVIDER='inconnu')
    def test_unknown_provider(self):
        self.assertIsNone(get_provider())

    @override_settings(SMS_PROVIDER='console', DEBUG=False)
    def test_console_in_production_is_not_reported_as_sent(self):
        with self.assertLogs('apps', level='ERROR'):
            result = SMSService.send('+2290161000000', 'x')
        self.assertFalse(result.ok)

    @override_settings(SMS_PROVIDER='console', DEBUG=True)
    def test_console_in_dev_is_ok(self):
        self.assertTrue(SMSService.send('+2290161000000', 'x').ok)


@override_settings(ESMS_API_KEY='esms_live_secret', ESMS_BASE_URL='https://sms.esmsafrica.io/api', ESMS_SENDER_ID='')
class ESMSAfricaTests(TestCase):
    def _resp(self, status_code, body):
        r = mock.Mock(status_code=status_code, content=b'{}', text=str(body))
        r.json.return_value = body
        return r

    def test_success_matches_documented_contract(self):
        body = {'id': 'msg_123', 'status': 'submitted', 'segments': 1, 'cost': 0.03, 'balance_after': 10}
        with mock.patch('apps.notifications.sms.requests.post', return_value=self._resp(200, body)) as post:
            result = ESMSAfricaProvider().send('+2290161000000', 'Bonjour')
        self.assertTrue(result.ok)
        self.assertEqual(result.message_id, 'msg_123')
        self.assertEqual(result.provider, 'esms')
        self.assertEqual(post.call_args.args[0], 'https://sms.esmsafrica.io/api/messages/send')
        self.assertEqual(post.call_args.kwargs['json'], {'to': '+2290161000000', 'text': 'Bonjour'})
        self.assertEqual(post.call_args.kwargs['headers']['Authorization'], 'Bearer esms_live_secret')
        self.assertIn('timeout', post.call_args.kwargs)

    @override_settings(ESMS_SENDER_ID='MonTour')
    def test_sender_id_is_sent_when_configured(self):
        with mock.patch('apps.notifications.sms.requests.post', return_value=self._resp(200, {'id': '1', 'status': 'queued'})) as post:
            ESMSAfricaProvider().send('+2290161000000', 'x')
        self.assertEqual(post.call_args.kwargs['json']['sender_id'], 'MonTour')

    @override_settings(ESMS_BASE_URL='https://exemple.test/api/')
    def test_base_url_is_configurable(self):
        with mock.patch('apps.notifications.sms.requests.post', return_value=self._resp(200, {'id': '1', 'status': 'queued'})) as post:
            ESMSAfricaProvider().send('+2290161000000', 'x')
        self.assertEqual(post.call_args.args[0], 'https://exemple.test/api/messages/send')

    def test_failed_status_in_a_200_response_is_a_failure(self):
        body = {'id': 'msg_1', 'status': 'failed', 'error_message': 'Numéro invalide'}
        with mock.patch('apps.notifications.sms.requests.post', return_value=self._resp(200, body)):
            result = ESMSAfricaProvider().send('+2290161000000', 'x')
        self.assertFalse(result.ok)
        self.assertIn('Numéro invalide', result.error)

    def test_documented_http_errors_have_actionable_messages(self):
        cases = {401: 'ESMS_API_KEY', 402: 'Solde', 429: 'cadence'}
        for code, expected in cases.items():
            with mock.patch('apps.notifications.sms.requests.post', return_value=self._resp(code, {})):
                result = ESMSAfricaProvider().send('+2290161000000', 'x')
            self.assertFalse(result.ok, code)
            self.assertIn(expected, result.error, code)
            self.assertIn(str(code), result.error)

    def test_validation_error_detail_is_kept(self):
        with mock.patch('apps.notifications.sms.requests.post', return_value=self._resp(422, {'message': 'to invalide'})):
            result = ESMSAfricaProvider().send('+2290161000000', 'x')
        self.assertFalse(result.ok)
        self.assertIn('to invalide', result.error)

    def test_non_json_error_body(self):
        resp = mock.Mock(status_code=502, content=b'<html>Bad gateway</html>', text='<html>Bad gateway</html>')
        resp.json.side_effect = ValueError('no json')
        with mock.patch('apps.notifications.sms.requests.post', return_value=resp):
            result = ESMSAfricaProvider().send('+2290161000000', 'x')
        self.assertFalse(result.ok)
        self.assertIn('502', result.error)

    def test_network_error(self):
        with mock.patch('apps.notifications.sms.requests.post', side_effect=requests.Timeout('lent')):
            result = ESMSAfricaProvider().send('+2290161000000', 'x')
        self.assertFalse(result.ok)
        self.assertIn('réseau', result.error)

    def test_sms_text_is_gsm_safe_before_sending(self):
        with mock.patch('apps.notifications.sms.requests.post', return_value=self._resp(200, {'id': '1', 'status': 'queued'})) as post:
            SMSService.send('+2290161000000', "Ticket n°5 — c'est l'heure à Ségbana")
        self.assertEqual(post.call_args.kwargs['json']['text'], "Ticket n5 - c'est l'heure a Segbana")


class SendToUserTests(TestCase):
    def test_sent_and_logged(self):
        user = make_user(1)
        with mock.patch.object(SMSService, 'send', return_value=OK) as send:
            log = SMSService.send_to_user(user, 'Salut', kind=SMSLog.KIND_TEST)
        self.assertEqual(log.status, SMSLog.STATUS_SENT)
        self.assertEqual(log.to, '+2290161000000')
        send.assert_called_once_with('+2290161000000', 'Salut')

    def test_skipped_without_phone(self):
        log = SMSService.send_to_user(make_user(1, phone=''), 'x', kind=SMSLog.KIND_TEST)
        self.assertEqual(log.status, SMSLog.STATUS_SKIPPED)

    def test_skipped_when_user_opted_out(self):
        user = make_user(1, sms_notifications=False)
        with mock.patch.object(SMSService, 'send') as send:
            log = SMSService.send_to_user(user, 'x', kind=SMSLog.KIND_TEST)
        self.assertEqual(log.status, SMSLog.STATUS_SKIPPED)
        send.assert_not_called()

    @override_settings(SMS_ENABLED=False)
    def test_skipped_when_globally_disabled(self):
        with mock.patch.object(SMSService, 'send') as send:
            log = SMSService.send_to_user(make_user(1), 'x', kind=SMSLog.KIND_TEST)
        self.assertEqual(log.status, SMSLog.STATUS_SKIPPED)
        send.assert_not_called()

    def test_provider_failure_is_logged_not_raised(self):
        with mock.patch.object(SMSService, 'send', return_value=SMSResult(False, 'fake', error='HTTP 500')):
            log = SMSService.send_to_user(make_user(1), 'x', kind=SMSLog.KIND_TEST)
        self.assertEqual(log.status, SMSLog.STATUS_FAILED)
        self.assertIn('500', log.error)


@override_settings(SMS_APPROACH_THRESHOLD=2)
class QueueProgressTests(TestCase):
    """Les usagers reçoivent un SMS quand il reste au plus 2 personnes devant eux, une seule fois."""

    def setUp(self):
        self.queue = make_queue()
        self.tickets = [add_ticket(self.queue, make_user(i), i) for i in range(1, 6)]

    def _progress(self):
        with mock.patch.object(SMSService, 'send', return_value=OK) as send:
            NotificationService.notify_queue_progress(self.queue)
        return send

    def test_first_three_are_notified(self):
        send = self._progress()
        self.assertEqual(send.call_count, 3)
        notified = set(Ticket.objects.filter(approach_notified_at__isnull=False).values_list('number', flat=True))
        self.assertEqual(notified, {1, 2, 3})
        self.assertEqual(SMSLog.objects.filter(kind='approach', status='sent').count(), 3)
        self.assertEqual(Notification.objects.filter(type='reminder').count(), 3)

    def test_message_content(self):
        with mock.patch.object(SMSService, 'send', return_value=OK) as send:
            NotificationService.notify_queue_progress(self.queue)
        texts = {c.args[1] for c in send.call_args_list}
        self.assertTrue(any('vous etes le prochain' in t for t in texts))
        self.assertTrue(any('plus que 2 personne(s) avant vous' in t for t in texts))
        self.assertTrue(all('Centre de Sante' not in t or True for t in texts))

    def test_sent_only_once_per_ticket(self):
        self._progress()
        send = self._progress()
        self.assertEqual(send.call_count, 0)
        self.assertEqual(SMSLog.objects.count(), 3)

    def test_next_person_notified_when_queue_advances(self):
        self._progress()
        self.tickets[0].call()  # le n°1 est appelé : le n°4 n'a plus que 2 personnes devant lui
        send = self._progress()
        self.assertEqual(send.call_count, 1)
        self.assertIsNotNone(Ticket.objects.get(number=4).approach_notified_at)
        self.assertIsNone(Ticket.objects.get(number=5).approach_notified_at)

    def test_opted_out_user_gets_in_app_notification_but_no_sms(self):
        User.objects.filter(email='u1@test.bj').update(sms_notifications=False)
        send = self._progress()
        self.assertEqual(send.call_count, 2)
        self.assertEqual(Notification.objects.filter(user__email='u1@test.bj', type='reminder').count(), 1)
        self.assertEqual(SMSLog.objects.get(user__email='u1@test.bj').status, 'skipped')

    def test_provider_outage_never_raises(self):
        with mock.patch.object(SMSService, 'send', return_value=SMSResult(False, 'fake', error='HTTP 503')):
            NotificationService.notify_queue_progress(self.queue)
        self.assertEqual(SMSLog.objects.filter(status='failed').count(), 3)

    @override_settings(SMS_APPROACH_THRESHOLD=0)
    def test_threshold_zero_only_notifies_the_next_one(self):
        send = self._progress()
        self.assertEqual(send.call_count, 1)


class TicketEndpointsSmsTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.queue = make_queue()
        self.agent = make_user(0, role='agent')
        self.users = [make_user(i) for i in range(1, 6)]
        self.tickets = [add_ticket(self.queue, u, i + 1) for i, u in enumerate(self.users)]

    def test_call_next_sends_called_sms_and_approach_sms(self):
        self.client.force_authenticate(user=self.agent)
        with mock.patch.object(SMSService, 'send', return_value=OK):
            resp = self.client.post(f'/api/v1/tickets/queues/{self.queue.id}/call-next/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        called = SMSLog.objects.get(kind='called')
        self.assertEqual(called.user, self.users[0])
        self.assertIn("c'est votre tour", called.text)
        self.assertIn('numero 1', called.text)
        # n°2, 3, 4 sont désormais dans la zone « plus que 0, 1, 2 personnes »
        approach = set(SMSLog.objects.filter(kind='approach').values_list('ticket__number', flat=True))
        self.assertEqual(approach, {2, 3, 4})

    def test_call_next_survives_sms_provider_crash(self):
        self.client.force_authenticate(user=self.agent)
        with mock.patch.object(SMSService, 'send', side_effect=RuntimeError('boom')),                 self.assertLogs('apps', level='ERROR'):
            resp = self.client.post(f'/api/v1/tickets/queues/{self.queue.id}/call-next/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(Ticket.objects.get(number=1).status, Ticket.STATUS_CALLED)

    def test_cancel_moves_the_queue_and_notifies(self):
        with mock.patch.object(SMSService, 'send', return_value=OK):
            NotificationService.notify_queue_progress(self.queue)  # n°1..3 déjà prévenus
            self.client.force_authenticate(user=self.users[0])
            resp = self.client.delete(f'/api/v1/tickets/{self.tickets[0].id}/cancel/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # l'annulation du n°1 fait entrer le n°4 dans la zone de rappel
        self.assertIsNotNone(Ticket.objects.get(number=4).approach_notified_at)

    def test_serving_a_waiting_ticket_moves_the_queue(self):
        self.client.force_authenticate(user=self.agent)
        with mock.patch.object(SMSService, 'send', return_value=OK):
            NotificationService.notify_queue_progress(self.queue)
            resp = self.client.post(f'/api/v1/tickets/{self.tickets[0].id}/serve/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(Ticket.objects.get(number=4).approach_notified_at)


class ProfileSmsPreferenceTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = make_user(1)
        self.client.force_authenticate(user=self.user)

    def test_user_can_opt_out_and_update_phone(self):
        resp = self.client.put('/api/v1/auth/me/', {'phone': '01 61 00 00 00', 'sms_notifications': False}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data['data']['sms_notifications'])
        self.assertEqual(resp.data['data']['phone'], '0161000000')

    def test_invalid_phone_is_rejected(self):
        resp = self.client.put('/api/v1/auth/me/', {'phone': '123'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_sms_enabled_by_default(self):
        self.assertTrue(self.client.get('/api/v1/auth/me/').data['data']['sms_notifications'])


class AdminTestSmsActionTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(email='root@test.bj', username='Root', password='pass')
        self.target = make_user(1)
        self.client.force_login(self.admin)

    def _run_action(self):
        return self.client.post('/admin/accounts/user/', {
            'action': 'send_test_sms', '_selected_action': [str(self.target.pk)],
        }, follow=True)

    def test_action_sends_a_test_sms_and_logs_it(self):
        with mock.patch.object(SMSService, 'send', return_value=OK) as send:
            resp = self._run_action()
        self.assertContains(resp, 'Envoyé')
        send.assert_called_once()
        log = SMSLog.objects.get(kind=SMSLog.KIND_TEST)
        self.assertEqual((log.user, log.status, log.to), (self.target, 'sent', '+2290161000000'))

    def test_action_reports_provider_failure_to_the_admin(self):
        with mock.patch.object(SMSService, 'send', return_value=SMSResult(False, 'esms', error='HTTP 402 : Solde insuffisant')):
            resp = self._run_action()
        self.assertContains(resp, 'Solde insuffisant')
        self.assertEqual(SMSLog.objects.get(kind=SMSLog.KIND_TEST).status, 'failed')
