# =============================================================
# MonTour — apps/accounts/models.py
# Modèles : User (personnalisé), UserProfile, FCMToken
# =============================================================

import uuid
import secrets
from datetime import timedelta
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """Manager personnalisé pour le modèle User."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('L\'adresse email est obligatoire')
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.ROLE_ADMIN)
        # Créé en ligne de commande par un opérateur : pas de confirmation par email
        extra_fields.setdefault('email_verified', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Modèle utilisateur personnalisé de MonTour.
    Remplace le User Django par défaut (AUTH_USER_MODEL).
    """

    # Rôles disponibles
    ROLE_USER  = 'user'
    ROLE_AGENT = 'agent'
    ROLE_ADMIN = 'admin'
    ROLE_CHOICES = [
        (ROLE_USER,  'Usager'),
        (ROLE_AGENT, 'Agent de service'),
        (ROLE_ADMIN, 'Administrateur'),
    ]

    # Niveaux de priorité
    PRIORITY_NORMAL   = 'normal'
    PRIORITY_SENIOR   = 'senior'
    PRIORITY_HANDICAP = 'handicap'
    PRIORITY_URGENT   = 'urgent'
    PRIORITY_CHOICES = [
        (PRIORITY_NORMAL,   'Normal'),
        (PRIORITY_SENIOR,   'Senior (60+ ans)'),
        (PRIORITY_HANDICAP, 'Personne handicapée'),
        (PRIORITY_URGENT,   'Urgence médicale'),
    ]

    # Champs
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email      = models.EmailField(unique=True, verbose_name='Adresse email')
    username   = models.CharField(max_length=100, verbose_name='Nom d\'utilisateur')
    phone      = models.CharField(max_length=20, blank=True, verbose_name='Téléphone')
    role       = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_USER)
    priority   = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default=PRIORITY_NORMAL)
    avatar     = models.ImageField(upload_to='avatars/', null=True, blank=True)

    # Champs de contrôle Django
    is_active     = models.BooleanField(default=True)
    is_staff      = models.BooleanField(default=False)
    date_joined   = models.DateTimeField(default=timezone.now)
    last_login    = models.DateTimeField(null=True, blank=True)

    # Vérification email
    email_verified = models.BooleanField(
        default=False,
        verbose_name='Email vérifié',
        help_text='L\'utilisateur a confirmé son adresse email.',
    )

    # Lien Firebase (pour l'auth Google OAuth)
    firebase_uid = models.CharField(max_length=128, blank=True, null=True, unique=True)

    objects = UserManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'mt_users'
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['priority']),
        ]

    def __str__(self):
        return f'{self.username} <{self.email}>'

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    @property
    def is_agent(self):
        return self.role == self.ROLE_AGENT

    @property
    def priority_score_base(self):
        from montour.utils import PriorityScorer
        return PriorityScorer.BASE_SCORES.get(self.priority, 40)


class FCMToken(models.Model):
    """
    Jeton Firebase Cloud Messaging pour notifications push.
    Un utilisateur peut avoir plusieurs appareils.
    """
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fcm_tokens')
    token      = models.TextField(unique=True, verbose_name='Token FCM')
    device_type = models.CharField(
        max_length=10,
        choices=[('android', 'Android'), ('ios', 'iOS'), ('web', 'Web')],
        default='android',
    )
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'mt_fcm_tokens'
        verbose_name = 'Token FCM'
        verbose_name_plural = 'Tokens FCM'

    def __str__(self):
        return f'FCM:{self.device_type} — {self.user.username}'


class PasswordResetToken(models.Model):
    """Token de réinitialisation de mot de passe."""
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_tokens')
    token      = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    used       = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'mt_password_reset_tokens'

    def is_valid(self):
        return not self.used and timezone.now() < self.expires_at


class EmailVerificationToken(models.Model):
    """Token de vérification d'adresse email."""
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.ForeignKey(
        'User', on_delete=models.CASCADE, related_name='email_verification_tokens'
    )
    token      = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    used       = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'mt_email_verification_tokens'
        verbose_name = 'Token de vérification email'
        verbose_name_plural = 'Tokens de vérification email'

    @classmethod
    def create_for_user(cls, user):
        """Génère et sauvegarde un nouveau token pour l'utilisateur."""
        # Invalider les anciens tokens non utilisés
        cls.objects.filter(user=user, used=False).update(used=True)
        token_str = secrets.token_urlsafe(32)
        expires = timezone.now() + timedelta(hours=24)
        return cls.objects.create(user=user, token=token_str, expires_at=expires)

    def is_valid(self):
        return not self.used and timezone.now() < self.expires_at