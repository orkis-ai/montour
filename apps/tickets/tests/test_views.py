# =============================================================
# MonTour — apps/tickets/tests/test_views.py
# Tests : Tickets et Files d'attente
# =============================================================

from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from apps.accounts.models import User
from apps.services.models import Service
from apps.queues.models import Queue
from apps.tickets.models import Ticket


def make_user(email='user@test.bj', role='user', priority='normal'):
    return User.objects.create_user(email=email, username='Test', password='pass', role=role, priority=priority)


def make_service(name='Santé'):
    s = Service.objects.create(name=name, avg_service_time=10)
    q = Queue.objects.create(service=s)
    return s, q


class TakeTicketTests(APITestCase):
    def setUp(self):
        self.user    = make_user()
        self.svc, self.queue = make_service()
        self.client.force_authenticate(user=self.user)

    def test_take_ticket_success(self):
        resp = self.client.post(f'/api/v1/tickets/take/{self.queue.id}/')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn('ticket', resp.data['data'])
        self.assertEqual(Ticket.objects.count(), 1)

    def test_take_ticket_twice_fails(self):
        self.client.post(f'/api/v1/tickets/take/{self.queue.id}/')
        resp = self.client.post(f'/api/v1/tickets/take/{self.queue.id}/')
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)

    def test_take_ticket_closed_queue(self):
        self.queue.close()
        resp = self.client.post(f'/api/v1/tickets/take/{self.queue.id}/')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_take_ticket_unknown_queue(self):
        import uuid
        resp = self.client.post(f'/api/v1/tickets/take/{uuid.uuid4()}/')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class CancelTicketTests(APITestCase):
    def setUp(self):
        self.user    = make_user()
        self.svc, self.queue = make_service()
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(f'/api/v1/tickets/take/{self.queue.id}/')
        self.ticket_id = resp.data['data']['ticket']['id']

    def test_cancel_waiting_ticket(self):
        resp = self.client.delete(f'/api/v1/tickets/{self.ticket_id}/cancel/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        ticket = Ticket.objects.get(pk=self.ticket_id)
        self.assertEqual(ticket.status, Ticket.STATUS_CANCELLED)

    def test_cancel_served_ticket_fails(self):
        ticket = Ticket.objects.get(pk=self.ticket_id)
        ticket.call()
        ticket.serve()
        resp = self.client.delete(f'/api/v1/tickets/{self.ticket_id}/cancel/')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class CallNextTests(APITestCase):
    def setUp(self):
        self.agent   = make_user('agent@test.bj', role='agent')
        self.normal  = make_user('normal@test.bj')
        self.urgent  = make_user('urgent@test.bj', priority='urgent')
        self.svc, self.queue = make_service()
        self.client.force_authenticate(user=self.normal)
        self.client.post(f'/api/v1/tickets/take/{self.queue.id}/')
        self.client.force_authenticate(user=self.urgent)
        self.client.post(f'/api/v1/tickets/take/{self.queue.id}/')

    def test_call_next_as_agent(self):
        self.client.force_authenticate(user=self.agent)
        resp = self.client.post(f'/api/v1/tickets/queues/{self.queue.id}/call-next/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        ticket = Ticket.objects.get(pk=resp.data['data']['id'])
        self.assertEqual(ticket.status, Ticket.STATUS_CALLED)

    def test_priority_ordering(self):
        """Le ticket URGENT doit être appelé avant NORMAL."""
        self.client.force_authenticate(user=self.agent)
        resp = self.client.post(f'/api/v1/tickets/queues/{self.queue.id}/call-next/')
        called_ticket = Ticket.objects.get(pk=resp.data['data']['id'])
        self.assertEqual(called_ticket.user.priority, 'urgent')

    def test_call_next_unauthorized(self):
        self.client.force_authenticate(user=self.normal)
        resp = self.client.post(f'/api/v1/tickets/queues/{self.queue.id}/call-next/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class TicketModelTests(TestCase):
    def setUp(self):
        self.user    = make_user()
        self.svc, self.queue = make_service()

    def _create_ticket(self):
        self.queue.current_number += 1
        self.queue.save()
        return Ticket.objects.create(queue=self.queue, user=self.user, number=self.queue.current_number)

    def test_call_ticket(self):
        t = self._create_ticket()
        t.call()
        self.assertEqual(t.status, Ticket.STATUS_CALLED)
        self.assertIsNotNone(t.called_at)

    def test_serve_ticket(self):
        t = self._create_ticket()
        t.call()
        t.serve()
        self.assertEqual(t.status, Ticket.STATUS_SERVED)
        self.assertIsNotNone(t.served_at)
        self.assertIsNotNone(t.actual_wait)

    def test_cancel_ticket(self):
        t = self._create_ticket()
        t.cancel()
        self.assertEqual(t.status, Ticket.STATUS_CANCELLED)
        self.assertIsNotNone(t.cancelled_at)

    def test_is_active_property(self):
        t = self._create_ticket()
        self.assertTrue(t.is_active)
        t.serve()
        self.assertFalse(t.is_active)


# =============================================================
# apps/queues/tests/test_models.py
# =============================================================

class QueueModelTests(TestCase):
    def setUp(self):
        self.svc, self.queue = make_service()

    def test_open_close(self):
        self.queue.open()
        self.assertEqual(self.queue.status, Queue.STATUS_OPEN)
        self.queue.close()
        self.assertEqual(self.queue.status, Queue.STATUS_CLOSED)

    def test_next_number(self):
        n1 = self.queue.next_number()
        n2 = self.queue.next_number()
        self.assertEqual(n1, 1)
        self.assertEqual(n2, 2)

    def test_waiting_count(self):
        user = make_user()
        Ticket.objects.create(queue=self.queue, user=user, number=1, status='waiting')
        Ticket.objects.create(queue=self.queue, user=user, number=2, status='served')
        self.assertEqual(self.queue.waiting_count, 1)

    def test_is_full(self):
        self.queue.max_capacity = 2
        self.queue.save()
        user = make_user()
        Ticket.objects.create(queue=self.queue, user=user, number=1, status='waiting')
        Ticket.objects.create(queue=self.queue, user=user, number=2, status='waiting')
        self.assertTrue(self.queue.is_full)