# =============================================================
# MonTour — Services et files d'attente par défaut (Ségbana)
#
# Vercel n'a pas d'étape de release : la base de production ne reçoit que les
# migrations (voir montour/wsgi.py). Sans cette migration de données, elle
# n'aurait aucun service ni aucune file, et l'application web ne pourrait
# proposer aucun ticket. Aucun compte n'est créé ici (contrairement à seed.py).
# Idempotente : un service déjà présent (même nom, avec ou sans emoji) est réutilisé.
# =============================================================

from django.db import migrations

DEFAULT_SERVICES = [
    {
        'name': 'Centre de Santé de Ségbana',
        'description': 'Consultations générales, urgences médicales et soins primaires de la commune de Ségbana.',
        'category': 'health', 'icon': '🏥', 'color': '#ef4444', 'avg_service_time': 12,
        'address': 'Quartier Administratif, Ségbana, Bénin',
    },
    {
        'name': 'Guichet Administratif (Mairie)',
        'description': "Délivrance d'actes d'état civil, légalisations et démarches administratives locales.",
        'category': 'admin', 'icon': '🏛️', 'color': '#3b82f6', 'avg_service_time': 8,
        'address': 'Mairie de Ségbana, Bénin',
    },
    {
        'name': 'Agence PEBCO Ségbana',
        'description': "Service de microfinance, épargne, crédit aux producteurs et transferts d'argent.",
        'category': 'finance', 'icon': '🏦', 'color': '#10b981', 'avg_service_time': 10,
        'address': 'Avenue du Marché, Ségbana, Bénin',
    },
    {
        'name': 'ATDA Pôle 4 Ségbana',
        'description': "Agence Territoriale de Développement Agricole — appui aux filières maïs, coton et élevage.",
        'category': 'agriculture', 'icon': '🌾', 'color': '#f59e0b', 'avg_service_time': 15,
        'address': 'Zone Agricole ATDA, Ségbana, Bénin',
    },
]


def create_default_services(apps, schema_editor):
    Service = apps.get_model('services', 'Service')
    ServiceHours = apps.get_model('services', 'ServiceHours')
    Queue = apps.get_model('queues', 'Queue')

    for data in DEFAULT_SERVICES:
        service = Service.objects.filter(name__startswith=data['name']).first()
        if service is None:
            service = Service.objects.create(**data)
        if not Queue.objects.filter(service=service).exists():
            Queue.objects.create(service=service, status='open', max_capacity=100)
        # Lun-Ven 8h-17h, samedi 8h-12h, dimanche fermé
        for day in range(7):
            ServiceHours.objects.get_or_create(
                service=service, day=day,
                defaults={
                    'open_time': '08:00',
                    'close_time': '17:00' if day < 5 else ('12:00' if day == 5 else '00:00'),
                    'is_open': day < 6,
                },
            )


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0001_initial'),
        ('queues', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_services, migrations.RunPython.noop),
    ]
