# =============================================================
# MonTour — apps/accounts/views.py
# Views : Register, Login, Logout, Profile, Password, FCMToken
# Avec validations et RLS côté serveur
# =============================================================

import secrets
import logging
from datetime import timedelta
from django.utils import timezone
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import AnonRateThrottle, ScopedRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, FCMToken, PasswordResetToken
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    UpdateProfileSerializer, ChangePasswordSerializer,
    TokenSerializer, FCMTokenSerializer, ForgotPasswordSerializer,
)
from montour.utils import api_response, api_error
from montour.permissions import IsAdminUser

logger = logging.getLogger('apps')


# ─── Throttle personnalisé pour l'authentification ────────────
class AuthRateThrottle(AnonRateThrottle):
    """Limite les tentatives d'authentification : 5/minute."""
    rate = '5/min'


# ─── POST /api/v1/auth/register/ ─────────────────────────────
class RegisterView(APIView):
    """
    Inscription d'un nouvel utilisateur.
    Crée le compte et retourne les tokens JWT.
    Validations : email strict, password fort, username, phone.
    """
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f'[REGISTER] Tentative d\'inscription invalide : {serializer.errors}')
            return api_error('Données d\'inscription invalides', details=serializer.errors)

        user = serializer.save()
        tokens = TokenSerializer.get_tokens(user)

        # Notification de bienvenue
        from apps.notifications.models import Notification
        Notification.objects.create(
            user=user,
            type=Notification.TYPE_INFO,
            title='🎉 Bienvenue sur MonTour !',
            message=f'Bonjour {user.username}, votre compte a été créé avec succès. '
                    f'Prenez votre premier ticket maintenant !',
        )

        logger.info(f'[REGISTER] Nouveau compte créé : {user.email}')

        return api_response(
            data={**tokens, 'user': UserSerializer(user, context={'request': request}).data},
            message='Compte créé avec succès.',
            status_code=status.HTTP_201_CREATED,
        )


# ─── POST /api/v1/auth/login/ ────────────────────────────────
class LoginView(APIView):
    """
    Authentification par email/password.
    Retourne access + refresh tokens JWT.
    Rate limited : 5 tentatives/minute max.
    """
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            logger.warning(f'[LOGIN] Tentative de connexion échouée depuis {request.META.get("REMOTE_ADDR")}')
            return api_error('Identifiants invalides', details=serializer.errors, status_code=401)

        user = serializer.validated_data['user']
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        tokens = TokenSerializer.get_tokens(user)
        logger.info(f'[LOGIN] Connexion réussie : {user.email}')

        return api_response(
            data={**tokens, 'user': UserSerializer(user, context={'request': request}).data},
            message='Connexion réussie.',
        )


# ─── POST /api/v1/auth/logout/ ───────────────────────────────
class LogoutView(APIView):
    """
    Déconnexion : blackliste le refresh token.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token or not isinstance(refresh_token, str):
                return api_error('Token refresh requis.', status_code=400)
            if len(refresh_token) > 1024:
                return api_error('Token refresh invalide.', status_code=400)
            token = RefreshToken(refresh_token)
            token.blacklist()
            logger.info(f'[LOGOUT] Déconnexion : {request.user.email}')
            return api_response(message='Déconnexion réussie.')
        except Exception:
            return api_error('Token invalide ou déjà révoqué.', status_code=400)


# ─── GET/PUT /api/v1/auth/me/ ────────────────────────────────
class ProfileView(APIView):
    """
    Récupération et mise à jour du profil utilisateur connecté.
    RLS : un utilisateur ne peut voir/modifier que SON profil.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user, context={'request': request})
        return api_response(data=serializer.data)

    def put(self, request):
        serializer = UpdateProfileSerializer(
            request.user, data=request.data, partial=True
        )
        if not serializer.is_valid():
            return api_error('Données de profil invalides', details=serializer.errors)

        serializer.save()
        logger.info(f'[PROFILE] Profil mis à jour : {request.user.email}')
        return api_response(
            data=UserSerializer(request.user, context={'request': request}).data,
            message='Profil mis à jour avec succès.',
        )


# ─── POST /api/v1/auth/change-password/ ──────────────────────
class ChangePasswordView(APIView):
    """
    Changement de mot de passe.
    Validations : ancien mot de passe vérifié, nouveau ≠ ancien,
    robustesse du nouveau (8+, majuscule, minuscule, chiffre, spécial).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={'request': request}
        )
        if not serializer.is_valid():
            return api_error('Erreur de validation', details=serializer.errors)

        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        logger.info(f'[PASSWORD] Mot de passe changé : {request.user.email}')
        return api_response(message='Mot de passe changé avec succès.')


# ─── POST /api/v1/auth/forgot-password/ ──────────────────────
class ForgotPasswordView(APIView):
    """
    Demande de réinitialisation de mot de passe.
    Sécurité : message générique (ne révèle pas si l'email existe).
    Rate limited pour éviter l'abus.
    """
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error('Email invalide', details=serializer.errors)

        email = serializer.validated_data['email']

        # Message générique : ne pas révéler si l'email existe (sécurité)
        generic_message = (
            'Si un compte est associé à cette adresse, '
            'un email de réinitialisation a été envoyé.'
        )

        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            # Ne PAS révéler que l'email n'existe pas
            logger.info(f'[FORGOT-PWD] Tentative avec email inexistant : {email}')
            return api_response(message=generic_message)

        token_str = secrets.token_urlsafe(32)
        expires = timezone.now() + timedelta(hours=2)

        PasswordResetToken.objects.create(user=user, token=token_str, expires_at=expires)

        # Envoi email (configurer EMAIL_* dans settings.py)
        try:
            from django.core.mail import send_mail
            reset_url = f"https://montour.bj/reset-password?token={token_str}"
            send_mail(
                subject='Réinitialisation de votre mot de passe MonTour',
                message=f'Cliquez sur le lien pour réinitialiser : {reset_url}\n\nLien valide 2 heures.',
                from_email='noreply@montour.bj',
                recipient_list=[email],
            )
        except Exception as e:
            logger.error(f'[FORGOT-PWD] Erreur envoi email : {e}')

        logger.info(f'[FORGOT-PWD] Token de reset généré pour : {email}')
        return api_response(message=generic_message)


# ─── GET /api/v1/auth/users/ (Admin seulement) ───────────────
class UserListView(generics.ListAPIView):
    """
    Liste tous les utilisateurs.
    RLS : Accès strictement réservé aux administrateurs.
    Les non-admins reçoivent une erreur 403.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        qs = User.objects.all()
        role = self.request.query_params.get('role')
        if role:
            # Validation whitelist du paramètre role
            valid_roles = [c[0] for c in User.ROLE_CHOICES]
            if role in valid_roles:
                qs = qs.filter(role=role)
        return qs


# ─── POST/DELETE /api/v1/auth/fcm-token/ ─────────────────────
class FCMTokenView(APIView):
    """
    Gestion des tokens Firebase Cloud Messaging.
    RLS : un utilisateur ne peut gérer que SES tokens.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = FCMTokenSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return api_error('Token FCM invalide', details=serializer.errors)
        token = serializer.save()
        return api_response(
            data=FCMTokenSerializer(token).data,
            message='Token FCM enregistré.',
            status_code=201,
        )

    def delete(self, request):
        token = request.data.get('token')
        if not token or not isinstance(token, str):
            return api_error('Token FCM requis.', status_code=400)
        if len(token) > 512:
            return api_error('Token FCM invalide.', status_code=400)
        # RLS : ne désactiver que les tokens de l'utilisateur connecté
        deleted = FCMToken.objects.filter(user=request.user, token=token).update(is_active=False)
        if deleted:
            return api_response(message='Token FCM désactivé.')
        return api_error('Token FCM introuvable.', status_code=404)