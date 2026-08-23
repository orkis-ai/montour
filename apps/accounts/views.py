# =============================================================
# MonTour — apps/accounts/views.py
# Views : Register, Login, Logout, Profile, Password, FCMToken
# =============================================================

import secrets
from datetime import timedelta
from django.utils import timezone
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, FCMToken, PasswordResetToken
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    UpdateProfileSerializer, ChangePasswordSerializer,
    TokenSerializer, FCMTokenSerializer, ForgotPasswordSerializer,
)
from montour.utils import api_response, api_error


# ─── POST /api/v1/auth/register/ ─────────────────────────────
class RegisterView(APIView):
    """
    Inscription d'un nouvel utilisateur.
    Crée le compte et retourne les tokens JWT.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
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
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return api_error('Identifiants invalides', details=serializer.errors, status_code=401)

        user = serializer.validated_data['user']
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        tokens = TokenSerializer.get_tokens(user)
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
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return api_response(message='Déconnexion réussie.')
        except Exception:
            return api_error('Token invalide ou déjà révoqué.', status_code=400)


# ─── GET/PUT /api/v1/auth/me/ ────────────────────────────────
class ProfileView(APIView):
    """
    Récupération et mise à jour du profil utilisateur connecté.
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
        return api_response(
            data=UserSerializer(request.user, context={'request': request}).data,
            message='Profil mis à jour avec succès.',
        )


# ─── POST /api/v1/auth/change-password/ ──────────────────────
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={'request': request}
        )
        if not serializer.is_valid():
            return api_error('Erreur de validation', details=serializer.errors)

        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return api_response(message='Mot de passe changé avec succès.')


# ─── POST /api/v1/auth/forgot-password/ ──────────────────────
class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error('Email invalide', details=serializer.errors)

        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        token_str = secrets.token_urlsafe(32)
        expires = timezone.now() + timedelta(hours=2)

        PasswordResetToken.objects.create(user=user, token=token_str, expires_at=expires)

        # Envoi email (configurer EMAIL_* dans settings.py)
        from django.core.mail import send_mail
        reset_url = f"https://montour.bj/reset-password?token={token_str}"
        send_mail(
            subject='Réinitialisation de votre mot de passe MonTour',
            message=f'Cliquez sur le lien pour réinitialiser : {reset_url}\n\nLien valide 2 heures.',
            from_email='noreply@montour.bj',
            recipient_list=[email],
        )
        return api_response(message='Email de réinitialisation envoyé.')


# ─── GET /api/v1/auth/users/ (Admin) ─────────────────────────
class UserListView(generics.ListAPIView):
    """Liste tous les utilisateurs (Admin seulement)."""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_admin:
            return User.objects.none()
        qs = User.objects.all()
        role = self.request.query_params.get('role')
        if role:
            qs = qs.filter(role=role)
        return qs


# ─── POST/DELETE /api/v1/auth/fcm-token/ ─────────────────────
class FCMTokenView(APIView):
    """Gestion des tokens Firebase Cloud Messaging."""
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
        if token:
            FCMToken.objects.filter(user=request.user, token=token).update(is_active=False)
        return api_response(message='Token FCM désactivé.')