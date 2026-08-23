# =============================================================
# MonTour — apps/services/tests/test_views.py
# =============================================================

from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from apps.accounts.models import User
from apps.services.models import Service


class ServiceTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='user@test.bj', username='UserTest', password='pass1234')
        self.admin = User.objects.create_superuser(email='admin@test.bj', username='AdminTest', password='pass1234')
        self.service = Service.objects.create(
            name='Centre de Santé de Ségbana 🏥',
            category=Service.CATEGORY_HEALTH,
            avg_service_time=12
        )

    def test_list_services_authenticated(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get('/api/v1/services/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_detail_service(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(f'/api/v1/services/{self.service.id}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        name = resp.data.get('data', {}).get('name') or resp.data.get('name')
        self.assertEqual(name, self.service.name)

    def test_create_service_admin_only(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post('/api/v1/services/create/', {'name': 'New Svc'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.admin)
        resp = self.client.post('/api/v1/services/create/', {'name': 'New Svc', 'category': 'admin', 'avg_service_time': 10}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
