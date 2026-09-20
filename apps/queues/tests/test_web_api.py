# =============================================================
# MonTour — apps/queues/tests/test_web_api.py
# Tests : API utilisée par l'application web (services, files, tickets)
# =============================================================

from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.queues.models import Queue
from apps.services.models import Service, ServiceHours
from apps.tickets.models import Ticket


def make_user(n, role='user', **extra):
    return User.objects.create_user(
        email=f'u{n}@test.bj', username=f'Usager {n}', password='pass', role=role,
        email_verified=True, **extra,
    )


class DefaultServicesTests(APITestCase):
    """La migration de données crée les services et files dont l'app web a besoin."""

    def test_default_services_and_queues_exist(self):
        names = set(Service.objects.values_list('name', flat=True))
        for expected in ['Centre de Santé de Ségbana', 'Guichet Administratif (Mairie)',
                         'Agence PEBCO Ségbana', 'ATDA Pôle 4 Ségbana']:
            self.assertIn(expected, names)
        for service in Service.objects.filter(name__in=names):
            self.assertTrue(Queue.objects.filter(service=service, status='open').exists(), service.name)
            self.assertEqual(ServiceHours.objects.filter(service=service).count(), 7)

    def test_no_account_is_created_by_the_migration(self):
        self.assertEqual(User.objects.count(), 0)

    def test_service_list_exposes_queue_id(self):
        self.client.force_authenticate(user=make_user(1))
        resp = self.client.get('/api/v1/services/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        first = resp.data['results'][0]
        self.assertEqual(first['queue_id'], str(Service.objects.get(pk=first['id']).queue.id))
        self.assertEqual(first['queue_status'], 'open')


class WebTicketFlowTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.service = Service.objects.get(name='Centre de Santé de Ségbana')
        self.queue = self.service.queue
        self.alice, self.bob = make_user(1), make_user(2)
        self.agent = make_user(3, role='agent')

    def _take(self, user):
        self.client.force_authenticate(user=user)
        resp = self.client.post(f'/api/v1/tickets/take/{self.queue.id}/')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        return resp.data['data']['ticket']

    def test_numbers_are_sequential_and_ticket_exposes_ids(self):
        t1, t2 = self._take(self.alice), self._take(self.bob)
        self.assertEqual((t1['number'], t2['number']), (1, 2))
        self.assertEqual(t1['service_id'], str(self.service.id))
        self.assertEqual(t1['queue_id'], str(self.queue.id))

    def test_mine_active_filter(self):
        ticket = self._take(self.alice)
        self.client.delete(f"/api/v1/tickets/{ticket['id']}/cancel/")
        self._take(self.alice)
        self.client.force_authenticate(user=self.alice)
        all_mine = self.client.get('/api/v1/tickets/mine/').data['results']
        active = self.client.get('/api/v1/tickets/mine/?active=1').data['results']
        self.assertEqual(len(all_mine), 2)
        self.assertEqual([t['status'] for t in active], ['waiting'])
        self.assertEqual(active[0]['position'], 1)

    def test_other_users_names_are_hidden_from_regular_users(self):
        self._take(self.alice)
        self._take(self.bob)
        self.client.force_authenticate(user=self.alice)
        tickets = self.client.get(f'/api/v1/queues/{self.service.id}/').data['data']['tickets']
        by_number = {t['number']: t for t in tickets}
        self.assertEqual(by_number[1]['user_name'], 'Usager 1')       # son propre nom
        self.assertTrue(by_number[1]['is_mine'])
        self.assertEqual(by_number[2]['user_name'], 'Usager')         # masqué
        self.assertFalse(by_number[2]['is_mine'])
        self.assertNotIn('Usager 2', str(tickets))

    def test_agent_sees_names(self):
        self._take(self.alice)
        self.client.force_authenticate(user=self.agent)
        tickets = self.client.get(f'/api/v1/queues/{self.service.id}/').data['data']['tickets']
        self.assertEqual(tickets[0]['user_name'], 'Usager 1')

    def test_agent_lists_waiting_and_called_tickets(self):
        self._take(self.alice)
        self.client.force_authenticate(user=self.agent)
        self.client.post(f'/api/v1/tickets/queues/{self.queue.id}/call-next/')
        called = self.client.get(f'/api/v1/tickets/queues/{self.queue.id}/?status=called').data['results']
        self.assertEqual([t['number'] for t in called], [1])

    def test_missed_flow(self):
        ticket = self._take(self.alice)
        self.client.force_authenticate(user=self.agent)
        # pas encore appelé : refusé
        self.assertEqual(self.client.post(f"/api/v1/tickets/{ticket['id']}/missed/").status_code, 400)
        self.client.post(f'/api/v1/tickets/queues/{self.queue.id}/call-next/')
        self.assertEqual(self.client.post(f"/api/v1/tickets/{ticket['id']}/missed/").status_code, 200)
        self.assertEqual(Ticket.objects.get(pk=ticket['id']).status, Ticket.STATUS_MISSED)

    def test_missed_is_reserved_to_agents(self):
        ticket = self._take(self.alice)
        self.client.force_authenticate(user=self.bob)
        self.assertEqual(self.client.post(f"/api/v1/tickets/{ticket['id']}/missed/").status_code, 403)
        self.client.force_authenticate(user=self.alice)
        self.assertEqual(self.client.post(f"/api/v1/tickets/{ticket['id']}/missed/").status_code, 403)

    def test_serve_called_ticket_then_take_a_new_one(self):
        ticket = self._take(self.alice)
        self.client.force_authenticate(user=self.agent)
        self.client.post(f'/api/v1/tickets/queues/{self.queue.id}/call-next/')
        self.assertEqual(self.client.post(f"/api/v1/tickets/{ticket['id']}/serve/").status_code, 200)
        again = self._take(self.alice)
        self.assertEqual(again['number'], 2)

    def test_queue_toggle_blocks_new_tickets(self):
        self.client.force_authenticate(user=self.agent)
        self.assertEqual(self.client.post(f'/api/v1/queues/{self.queue.id}/toggle/').data['data']['status'], 'closed')
        self.client.force_authenticate(user=self.alice)
        resp = self.client.post(f'/api/v1/tickets/take/{self.queue.id}/')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_notifications_reach_the_user_through_the_api(self):
        self._take(self.alice)
        self.client.force_authenticate(user=self.alice)
        self.assertEqual(self.client.get('/api/v1/notifications/unread-count/').data['data']['unread_count'], 1)
        items = self.client.get('/api/v1/notifications/').data['results']
        self.assertEqual(items[0]['type'], 'ticket_taken')
        self.client.put('/api/v1/notifications/read-all/')
        self.assertEqual(self.client.get('/api/v1/notifications/unread-count/').data['data']['unread_count'], 0)
