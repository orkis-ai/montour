# =============================================================
# MonTour — apps/queues/tests/test_views.py
# =============================================================

from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from apps.accounts.models import User
from apps.services.models import Service
from apps.queues.models import Queue


class QueueTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='user@test.bj', username='UserTest', password='pass1234')
        self.agent = User.objects.create_user(email='agent@test.bj', username='AgentTest', password='pass1234', role=User.ROLE_AGENT)
        self.service = Service.objects.create(name='Mairie de Ségbana 🏛️', category='admin')
        self.queue = Queue.objects.create(service=self.service, status=Queue.STATUS_OPEN)

    def test_list_queues(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get('/api/v1/queues/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_detail_queue(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(f'/api/v1/queues/{self.service.id}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_toggle_queue_permission(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(f'/api/v1/queues/{self.queue.id}/toggle/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.agent)
        resp = self.client.post(f'/api/v1/queues/{self.queue.id}/toggle/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['data']['status'], 'closed')
