# =============================================================
# MonTour — apps/accounts/serializers.py
# Serializers : Register, Login, User, Profile, FCMToken
# Avec validations strictes côté serveur
# =============================================================

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, FCMToken
from montour.validators import (
    validate_email_strict, validate_password_strength,
    validate_username, validate_phone_benin,
)


# ─── Serializer d'inscription ────────────────────────────────
class RegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, min_length=8, max_length=128, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, max_length=128, style={'input_type': 'password'}, label='Confirmer le mot de passe')

    class Meta:
        model  = User
        fields = ['username', 'email', 'phone', 'password', 'password2', 'priority']
        extra_kwargs = {
            'priority': {'default': User.PRIORITY_NORMAL},
        }

    def validate_email(self, value):
        """Validation stricte de l'email : format, domaine, unicité."""
        value = validate_email_strict(value)
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Cette adresse email est déjà utilisée.')
        return value

    def validate_username(self, value):
        """Validation du nom d'utilisateur : 3-50 chars, pas de caractères dangereux."""
        return validate_username(value)

    def validate_phone(self, value):
        """Validation du téléphone béninois."""
        return validate_phone_benin(value)

    def validate_password(self, value):
        """Validation robustesse du mot de passe."""
        validate_password_strength(value)
        # Utiliser aussi les validators Django (dictionnaire commun, etc.)
        validate_password(value)
        return value

    def validate_priority(self, value):
        """Validation stricte de la priorité via whitelist."""
        valid = [c[0] for c in User.PRIORITY_CHOICES]
        if value and value not in valid:
            raise serializers.ValidationError(
                f'Priorité invalide. Valeurs acceptées : {", ".join(valid)}'
            )
        return value or User.PRIORITY_NORMAL

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password2'):
            raise serializers.ValidationError({'password2': 'Les mots de passe ne correspondent pas.'})
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


# ─── Serializer de connexion ──────────────────────────────────
class LoginSerializer(serializers.Serializer):
    email    = serializers.EmailField(max_length=254)
    password = serializers.CharField(write_only=True, max_length=128, style={'input_type': 'password'})

    def validate_email(self, value):
        """Normalisation et validation basique de l'email."""
        if not value or not isinstance(value, str):
            raise serializers.ValidationError('Adresse email requise.')
        return value.strip().lower()

    def validate_password(self, value):
        """Vérifie que le mot de passe n'est pas vide."""
        if not value or not value.strip():
            raise serializers.ValidationError('Mot de passe requis.')
        return value

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get('request'),
            username=attrs['email'],
            password=attrs['password'],
        )
        if not user:
            raise serializers.ValidationError('Email ou mot de passe incorrect.')
        if not user.is_active:
            raise serializers.ValidationError('Ce compte est désactivé.')
        if not user.email_verified:
            raise serializers.ValidationError(
                {'email_not_verified': 'Votre adresse email n\'a pas encore été vérifiée. '
                 'Consultez votre boîte mail ou demandez un renvoi.'}
            )
        attrs['user'] = user
        return attrs


# ─── Serializer Profil utilisateur (lecture) ─────────────────
class UserSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = [
            'id', 'username', 'email', 'phone', 'role',
            'priority', 'avatar_url', 'email_verified', 'sms_notifications',
            'date_joined', 'last_login',
        ]
        read_only_fields = ['id', 'email', 'role', 'date_joined', 'last_login', 'email_verified']

    def get_avatar_url(self, obj):
        request = self.context.get('request')
        if obj.avatar and request:
            return request.build_absolute_uri(obj.avatar.url)
        return None


# ─── Serializer Mise à jour du profil ────────────────────────
class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['username', 'phone', 'priority', 'avatar', 'sms_notifications']

    def validate_username(self, value):
        """Validation du nom d'utilisateur."""
        return validate_username(value)

    def validate_phone(self, value):
        """Validation du téléphone béninois."""
        return validate_phone_benin(value)

    def validate_priority(self, value):
        """Validation stricte de la priorité via whitelist."""
        valid = [c[0] for c in User.PRIORITY_CHOICES]
        if value not in valid:
            raise serializers.ValidationError(
                f'Priorité invalide. Valeurs acceptées : {", ".join(valid)}'
            )
        return value

    def validate_avatar(self, value):
        """Validation du fichier avatar : taille et type MIME."""
        if value:
            # Taille max 2 Mo
            if value.size > 2 * 1024 * 1024:
                raise serializers.ValidationError('L\'avatar ne peut pas dépasser 2 Mo.')
            # Types MIME autorisés
            allowed_types = ['image/jpeg', 'image/png', 'image/webp']
            if hasattr(value, 'content_type') and value.content_type not in allowed_types:
                raise serializers.ValidationError(
                    'Format d\'image non supporté. Utilisez JPEG, PNG ou WebP.'
                )
        return value


# ─── Serializer changement de mot de passe ───────────────────
class ChangePasswordSerializer(serializers.Serializer):
    old_password  = serializers.CharField(write_only=True, max_length=128)
    new_password  = serializers.CharField(write_only=True, min_length=8, max_length=128)
    new_password2 = serializers.CharField(write_only=True, max_length=128)

    def validate_new_password(self, value):
        """Validation robustesse du nouveau mot de passe."""
        validate_password_strength(value)
        validate_password(value)
        return value

    def validate(self, attrs):
        user = self.context['request'].user

        # Vérifier l'ancien mot de passe
        if not user.check_password(attrs['old_password']):
            raise serializers.ValidationError({'old_password': 'Mot de passe actuel incorrect.'})

        # Vérifier que les deux nouveaux correspondent
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({'new_password2': 'Les nouveaux mots de passe ne correspondent pas.'})

        # Vérifier que le nouveau est différent de l'ancien
        if attrs['old_password'] == attrs['new_password']:
            raise serializers.ValidationError(
                {'new_password': 'Le nouveau mot de passe doit être différent de l\'ancien.'}
            )

        return attrs


# ─── Serializer réinitialisation de mot de passe (lien reçu par email) ───
class ResetPasswordSerializer(serializers.Serializer):
    token     = serializers.CharField(max_length=128)
    password  = serializers.CharField(write_only=True, min_length=8, max_length=128)
    password2 = serializers.CharField(write_only=True, max_length=128)

    def validate_password(self, value):
        validate_password_strength(value)
        validate_password(value)
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password2'):
            raise serializers.ValidationError({'password2': 'Les mots de passe ne correspondent pas.'})
        return attrs


# ─── Serializer Token JWT ────────────────────────────────────
class TokenSerializer(serializers.Serializer):
    """Retourné après login/register avec access + refresh tokens."""
    access   = serializers.CharField(read_only=True)
    refresh  = serializers.CharField(read_only=True)
    user     = UserSerializer(read_only=True)

    @staticmethod
    def get_tokens(user):
        refresh = RefreshToken.for_user(user)
        return {
            'access':  str(refresh.access_token),
            'refresh': str(refresh),
        }


# ─── Serializer Token FCM ────────────────────────────────────
class FCMTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model  = FCMToken
        fields = ['id', 'token', 'device_type', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_token(self, value):
        """Validation du token FCM : longueur et format."""
        if not value or not isinstance(value, str):
            raise serializers.ValidationError('Token FCM requis.')
        value = value.strip()
        if len(value) < 20:
            raise serializers.ValidationError('Token FCM trop court.')
        if len(value) > 512:
            raise serializers.ValidationError('Token FCM trop long (max 512 caractères).')
        return value

    def validate_device_type(self, value):
        """Validation du type d'appareil via whitelist."""
        valid = ['android', 'ios', 'web']
        if value not in valid:
            raise serializers.ValidationError(
                f'Type d\'appareil invalide. Valeurs acceptées : {", ".join(valid)}'
            )
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        # Upsert : update si le token existe déjà
        token, _ = FCMToken.objects.update_or_create(
            token=validated_data['token'],
            defaults={**validated_data, 'user': user, 'is_active': True},
        )
        return token


# ─── Serializer réinitialisation mot de passe ────────────────
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)

    def validate_email(self, value):
        """
        Validation email stricte.
        NOTE : On ne révèle PAS si l'email existe ou non (sécurité).
        La validation ici normalise simplement l'email.
        """
        return validate_email_strict(value)