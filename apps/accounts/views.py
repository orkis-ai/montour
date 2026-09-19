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
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, FCMToken, PasswordResetToken, EmailVerificationToken
from .emails import send_verification_email, send_password_reset_email
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    UpdateProfileSerializer, ChangePasswordSerializer,
    TokenSerializer, FCMTokenSerializer, ForgotPasswordSerializer, ResetPasswordSerializer,
)
from montour.utils import api_response, api_error
from montour.permissions import IsAdminUser

logger = logging.getLogger('apps')


# ─── Throttles d'authentification ────────────────────────────
# Chaque `scope` a son propre compteur (par IP) : sans cela, ils partageraient
# celui du throttle anonyme global et une inscription + une connexion + un
# renvoi d'email épuiseraient ensemble la limite de 5/minute.
class AuthRateThrottle(AnonRateThrottle):
    """Connexion : 5/minute."""
    scope = 'auth'


class RegisterRateThrottle(AnonRateThrottle):
    scope = 'register'


class ResendRateThrottle(AnonRateThrottle):
    scope = 'resend'


class RecoveryRateThrottle(AnonRateThrottle):
    """Mot de passe oublié + réinitialisation."""
    scope = 'recovery'


# ─── POST /api/v1/auth/register/ ─────────────────────────────
class RegisterView(APIView):
    """
    Inscription d'un nouvel utilisateur.
    Crée le compte (inactif tant que l'email n'est pas confirmé) et envoie
    le lien de vérification : aucun token JWT n'est renvoyé ici.
    Validations : email strict, password fort, username, phone.
    """
    permission_classes = [AllowAny]
    throttle_classes = [RegisterRateThrottle]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f'[REGISTER] Tentative d\'inscription invalide : {serializer.errors}')
            return api_error('Données d\'inscription invalides', details=serializer.errors)

        user = serializer.save()

        # Le compte reste inutilisable tant que l'email n'est pas confirmé
        email_sent = send_verification_email(request, user)

        # Notification de bienvenue
        from apps.notifications.models import Notification
        Notification.objects.create(
            user=user,
            type=Notification.TYPE_INFO,
            title='🎉 Bienvenue sur MonTour !',
            message=f'Bonjour {user.username}, votre compte a été créé avec succès. '
                    f'Vérifiez votre email pour activer votre compte !',
        )

        logger.info(f'[REGISTER] Nouveau compte créé : {user.email}')

        return api_response(
            data={
                'email': user.email,
                'email_verified': False,
                'email_sent': email_sent,
            },
            message=(
                'Compte créé. Un email de vérification a été envoyé.'
                if email_sent else
                "Compte créé, mais l'email de vérification n'a pas pu être envoyé. Demandez un renvoi."
            ),
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
            # Détecter spécifiquement l'email non vérifié
            if 'email_not_verified' in serializer.errors:
                return api_error(
                    'Email non vérifié. Consultez votre boîte mail ou demandez un renvoi.',
                    details={'email_not_verified': True, 'email': request.data.get('email', '')},
                    status_code=403,
                )
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
    throttle_classes = [RecoveryRateThrottle]

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

        # Un seul lien valide à la fois : les demandes précédentes sont invalidées
        PasswordResetToken.objects.filter(user=user, used=False).update(used=True)
        token_str = secrets.token_urlsafe(32)
        expires = timezone.now() + timedelta(hours=2)
        PasswordResetToken.objects.create(user=user, token=token_str, expires_at=expires)

        send_password_reset_email(request, user, token_str)

        logger.info(f'[FORGOT-PWD] Token de reset généré pour : {email}')
        return api_response(message=generic_message)


# ─── POST /api/v1/auth/reset-password/ ───────────────────────
class ResetPasswordView(APIView):
    """
    Choix d'un nouveau mot de passe avec le token reçu par email.
    POST /api/v1/auth/reset-password/  { token, password, password2 }
    Le lien a été reçu dans la boîte mail : cela prouve la possession de
    l'adresse, qui est donc aussi marquée comme vérifiée.
    """
    permission_classes = [AllowAny]
    throttle_classes = [RecoveryRateThrottle]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error('Données invalides', details=serializer.errors)

        try:
            token = PasswordResetToken.objects.select_related('user').get(
                token=serializer.validated_data['token']
            )
        except PasswordResetToken.DoesNotExist:
            return api_error('Lien invalide ou déjà utilisé.', status_code=400)

        if not token.is_valid() or not token.user.is_active:
            return api_error(
                'Ce lien a expiré ou a déjà été utilisé. Refaites une demande de réinitialisation.',
                status_code=400,
            )

        user = token.user
        user.set_password(serializer.validated_data['password'])
        user.email_verified = True
        user.save(update_fields=['password', 'email_verified'])
        PasswordResetToken.objects.filter(user=user, used=False).update(used=True)

        logger.info(f'[RESET-PWD] Mot de passe réinitialisé : {user.email}')
        return api_response(message='Mot de passe modifié. Vous pouvez vous connecter.')


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


# ─── POST /api/v1/auth/verify-email/ ──────────────────────
class VerifyEmailView(APIView):
    """
    Validation du token de vérification email.
    POST /api/v1/auth/verify-email/  { "token": "<token>" }
    Si le token est valide, active le compte et retourne les JWT.
    POST (et non GET) : un lien ouvert par un antivirus ou un aperçu de client
    mail ne doit pas consommer le token.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        token_str = request.data.get('token', '')
        if not isinstance(token_str, str) or not token_str.strip():
            return api_error('Token manquant.', status_code=400)
        token_str = token_str.strip()
        if len(token_str) > 128:
            return api_error('Token invalide.', status_code=400)

        try:
            token = EmailVerificationToken.objects.select_related('user').get(token=token_str)
        except EmailVerificationToken.DoesNotExist:
            return api_error('Lien invalide ou déjà utilisé.', status_code=400)

        if not token.is_valid():
            return api_error(
                'Ce lien de vérification a expiré ou a déjà été utilisé. Demandez un nouveau lien.',
                status_code=400,
            )

        user = token.user
        if not user.is_active:
            return api_error('Ce compte est désactivé.', status_code=403)

        user.email_verified = True
        user.last_login = timezone.now()
        user.save(update_fields=['email_verified', 'last_login'])

        token.used = True
        token.save(update_fields=['used'])

        # Connecter automatiquement l'utilisateur
        tokens = TokenSerializer.get_tokens(user)
        logger.info(f'[VERIFY-EMAIL] Email vérifié avec succès : {user.email}')

        return api_response(
            data={**tokens, 'user': UserSerializer(user, context={'request': request}).data},
            message='Email vérifié avec succès. Bienvenue sur MonTour !',
        )


# ─── POST /api/v1/auth/resend-verification/ ────────────────
class ResendVerificationView(APIView):
    """
    Renvoie l'email de vérification.
    POST /api/v1/auth/resend-verification/  { "email": "user@example.com" }
    Sécurité : réponse identique que le compte existe, soit déjà vérifié ou non
    (ne révèle pas quelles adresses sont inscrites).
    """
    permission_classes = [AllowAny]
    throttle_classes = [ResendRateThrottle]

    def post(self, request):
        email = request.data.get('email', '')
        if not isinstance(email, str) or not email.strip():
            return api_error('Email requis.', status_code=400)
        email = email.strip().lower()

        user = User.objects.filter(email=email, is_active=True, email_verified=False).first()
        if user:
            send_verification_email(request, user, resend=True)

        return api_response(message=(
            'Si un compte non vérifié est associé à cette adresse, '
            'un nouvel email de vérification a été envoyé.'
        ))
