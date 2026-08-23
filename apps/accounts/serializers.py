# =============================================================
# MonTour — apps/accounts/serializers.py
# Serializers : Register, Login, User, Profile, FCMToken
# =============================================================

from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, FCMToken


# ─── Serializer d'inscription ────────────────────────────────
class RegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, style={'input_type': 'password'}, label='Confirmer le mot de passe')

    class Meta:
        model  = User
        fields = ['username', 'email', 'phone', 'password', 'password2', 'priority']
        extra_kwargs = {
            'priority': {'default': User.PRIORITY_NORMAL},
        }

    def validate_email(self, value):
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError('Cette adresse email est déjà utilisée.')
        return value.lower()

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password2'):
            raise serializers.ValidationError({'password2': 'Les mots de passe ne correspondent pas.'})
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


# ─── Serializer de connexion ──────────────────────────────────
class LoginSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get('request'),
            username=attrs['email'].lower(),
            password=attrs['password'],
        )
        if not user:
            raise serializers.ValidationError('Email ou mot de passe incorrect.')
        if not user.is_active:
            raise serializers.ValidationError('Ce compte est désactivé.')
        attrs['user'] = user
        return attrs


# ─── Serializer Profil utilisateur (lecture) ─────────────────
class UserSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = [
            'id', 'username', 'email', 'phone', 'role',
            'priority', 'avatar_url', 'date_joined', 'last_login',
        ]
        read_only_fields = ['id', 'email', 'role', 'date_joined', 'last_login']

    def get_avatar_url(self, obj):
        request = self.context.get('request')
        if obj.avatar and request:
            return request.build_absolute_uri(obj.avatar.url)
        return None


# ─── Serializer Mise à jour du profil ────────────────────────
class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['username', 'phone', 'priority', 'avatar']

    def validate_priority(self, value):
        valid = [c[0] for c in User.PRIORITY_CHOICES]
        if value not in valid:
            raise serializers.ValidationError(f'Priorité invalide. Choisissez parmi : {valid}')
        return value


# ─── Serializer changement de mot de passe ───────────────────
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password2 = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = self.context['request'].user
        if not user.check_password(attrs['old_password']):
            raise serializers.ValidationError({'old_password': 'Mot de passe actuel incorrect.'})
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({'new_password2': 'Les nouveaux mots de passe ne correspondent pas.'})
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
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value.lower(), is_active=True).exists():
            raise serializers.ValidationError('Aucun compte actif trouvé avec cet email.')
        return value.lower()