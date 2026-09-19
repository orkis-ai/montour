# =============================================================
# MonTour — seed.py
# Script de peuplement initial de la base de données
# =============================================================

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'montour.settings')
django.setup()

from django.utils import timezone
from apps.accounts.models import User
from apps.services.models import Service, ServiceHours
from apps.queues.models import Queue
from apps.tickets.models import Ticket
from apps.notifications.models import Notification
from montour.utils import PriorityScorer, WaitTimePredictor


def seed():
    print("[+] Demarrage du peuplement de la base MonTour...")

    # 1. Création des utilisateurs
    print("  -- Creation des comptes utilisateurs...")
    admin_user, created = User.objects.get_or_create(
        email='admin@montour.bj',
        defaults={
            'email_verified': True,
            'username': 'Admin Ségbana',
            'phone': '+229 97000001',
            'role': User.ROLE_ADMIN,
            'is_staff': True,
            'is_superuser': True,
        }
    )
    if created:
        admin_user.set_password('admin1234')
        admin_user.save()

    agent_user, created = User.objects.get_or_create(
        email='agent@montour.bj',
        defaults={
            'email_verified': True,
            'username': 'Agent Guichet Ségbana',
            'phone': '+229 97000002',
            'role': User.ROLE_AGENT,
            'is_staff': True,
        }
    )
    if created:
        agent_user.set_password('agent1234')
        agent_user.save()

    normal_user, created = User.objects.get_or_create(
        email='oroukarga@gmail.com',
        defaults={
            'email_verified': True,
            'username': 'Ismaïla OROU KARGA',
            'phone': '+229 96123456',
            'role': User.ROLE_USER,
            'priority': User.PRIORITY_NORMAL,
        }
    )
    if created:
        normal_user.set_password('user1234')
        normal_user.save()

    senior_user, created = User.objects.get_or_create(
        email='senior@montour.bj',
        defaults={
            'email_verified': True,
            'username': 'El-Hadj Adamou (Senior)',
            'phone': '+229 97112233',
            'role': User.ROLE_USER,
            'priority': User.PRIORITY_SENIOR,
        }
    )
    if created:
        senior_user.set_password('senior1234')
        senior_user.save()

    handicap_user, created = User.objects.get_or_create(
        email='handicap@montour.bj',
        defaults={
            'email_verified': True,
            'username': 'Bio Bio Mariam (PMR)',
            'phone': '+229 97445566',
            'role': User.ROLE_USER,
            'priority': User.PRIORITY_HANDICAP,
        }
    )
    if created:
        handicap_user.set_password('handicap1234')
        handicap_user.save()

    urgent_user, created = User.objects.get_or_create(
        email='urgent@montour.bj',
        defaults={
            'email_verified': True,
            'username': 'Salifou Kandi (Urgence)',
            'phone': '+229 97778899',
            'role': User.ROLE_USER,
            'priority': User.PRIORITY_URGENT,
        }
    )
    if created:
        urgent_user.set_password('urgent1234')
        urgent_user.save()

    # 2. Création des services et leurs files
    print("  -- Creation des services et files d'attente a Segbana...")
    services_data = [
        {
            'name': 'Centre de Santé de Ségbana 🏥',
            'description': 'Consultations générales, urgences médicales et soins primaires de la commune de Ségbana.',
            'category': Service.CATEGORY_HEALTH,
            'icon': '🏥',
            'color': '#ef4444',
            'avg_service_time': 12,
            'address': 'Quartier Administratif, Ségbana, Bénin',
            'phone': '+229 21301001',
        },
        {
            'name': 'Guichet Administratif (Mairie) 🏛️',
            'description': 'Délivrance d\'actes d\'état civil, légalisations et démarches administratives locales.',
            'category': Service.CATEGORY_ADMIN,
            'icon': '🏛️',
            'color': '#3b82f6',
            'avg_service_time': 8,
            'address': 'Mairie de Ségbana, Bénin',
            'phone': '+229 21301002',
        },
        {
            'name': 'Agence PEBCO Ségbana 🏦',
            'description': 'Service de microfinance, épargne, crédit aux producteurs et transferts d\'argent.',
            'category': Service.CATEGORY_FINANCE,
            'icon': '🏦',
            'color': '#10b981',
            'avg_service_time': 10,
            'address': 'Avenue du Marché, Ségbana, Bénin',
            'phone': '+229 21301003',
        },
        {
            'name': 'ATDA Pôle 4 Ségbana 🌾',
            'description': 'Agence Territoriale de Développement Agricole — Appui aux filières maïs, coton et élevage.',
            'category': Service.CATEGORY_AGRICULTURE,
            'icon': '🌾',
            'color': '#f59e0b',
            'avg_service_time': 15,
            'address': 'Zone Agricole ATDA, Ségbana, Bénin',
            'phone': '+229 21301004',
        },
    ]

    for sdata in services_data:
        service, _ = Service.objects.get_or_create(name=sdata['name'], defaults=sdata)

        # Horaires (Lun-Ven 8h-17h, Sam 8h-12h)
        for day in range(7):
            open_t = '08:00'
            close_t = '17:00' if day < 5 else ('12:00' if day == 5 else '00:00')
            is_open = day < 6
            ServiceHours.objects.get_or_create(
                service=service, day=day,
                defaults={'open_time': open_t, 'close_time': close_t, 'is_open': is_open}
            )

        # File d'attente
        queue, _ = Queue.objects.get_or_create(
            service=service,
            defaults={'status': Queue.STATUS_OPEN, 'max_capacity': 100}
        )
        if queue.status != Queue.STATUS_OPEN:
            queue.status = Queue.STATUS_OPEN
            queue.save()

    # 3. Création des tickets de démonstration
    print("  -- Generation des tickets et notifications de test...")
    sante = Service.objects.get(name__icontains='Santé')
    queue_sante = sante.queue

    # Tickets d'exemple
    t_demo_users = [
        (normal_user, 'normal'),
        (senior_user, 'senior'),
        (handicap_user, 'handicap'),
        (urgent_user, 'urgent'),
    ]

    for u, prio in t_demo_users:
        if not Ticket.objects.filter(queue=queue_sante, user=u, status='waiting').exists():
            num = queue_sante.next_number()
            score = PriorityScorer.compute(prio, timezone.now())
            waiting_count = queue_sante.waiting_count + 1
            estimated = WaitTimePredictor.predict(sante, waiting_count, prio)

            t = Ticket.objects.create(
                queue=queue_sante,
                user=u,
                number=num,
                priority=prio,
                priority_score=score,
                estimated_wait=estimated,
            )

            Notification.objects.create(
                user=u,
                type=Notification.TYPE_TICKET_TAKEN,
                title='Ticket reserve !',
                message=f'Ticket n°{num} confirme - {sante.name}. Temps estime : ~{estimated} min.',
                ticket=t,
            )

    print("[+] Base de donnees initialisee avec succes avec donnees reelles pour Segbana !")


if __name__ == '__main__':
    seed()
