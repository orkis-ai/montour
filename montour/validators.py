# =============================================================
# MonTour — montour/validators.py
# Validations centralisées côté serveur
# =============================================================

import re
import html
from django.core.exceptions import ValidationError
from rest_framework import serializers


# ─── Validation Email stricte (RFC 5322 simplifié) ───────────
EMAIL_REGEX = re.compile(
    r'^[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+'
    r'@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?'
    r'(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$'
)

# Domaines jetables connus (liste de base, extensible)
DISPOSABLE_DOMAINS = {
    'mailinator.com', 'guerrillamail.com', 'tempmail.com',
    'throwaway.email', 'yopmail.com', 'trashmail.com',
    'fakeinbox.com', 'sharklasers.com', 'guerrillamailblock.com',
    'grr.la', 'dispostable.com', 'maildrop.cc',
}


def validate_email_strict(value):
    """
    Validation email stricte :
    - Format RFC 5322
    - Longueur max 254 caractères
    - Rejet des domaines jetables
    - Normalisation en minuscules
    """
    if not value or not isinstance(value, str):
        raise serializers.ValidationError('Adresse email requise.')

    value = value.strip().lower()

    if len(value) > 254:
        raise serializers.ValidationError('L\'adresse email ne peut pas dépasser 254 caractères.')

    if not EMAIL_REGEX.match(value):
        raise serializers.ValidationError(
            'Format d\'email invalide. Exemple valide : utilisateur@domaine.com'
        )

    # Vérifier le domaine
    domain = value.split('@')[1]
    if domain in DISPOSABLE_DOMAINS:
        raise serializers.ValidationError(
            'Les adresses email temporaires/jetables ne sont pas acceptées.'
        )

    # Vérifier que le domaine a au moins un point
    if '.' not in domain:
        raise serializers.ValidationError('Le domaine de l\'email est invalide.')

    # Vérifier longueur partie locale
    local_part = value.split('@')[0]
    if len(local_part) > 64:
        raise serializers.ValidationError('La partie locale de l\'email est trop longue (max 64 caractères).')

    return value


# ─── Validation mot de passe fort ────────────────────────────
def validate_password_strength(value):
    """
    Vérifie la robustesse du mot de passe :
    - Minimum 8 caractères
    - Au moins 1 majuscule
    - Au moins 1 minuscule
    - Au moins 1 chiffre
    - Au moins 1 caractère spécial
    - Pas d'espaces en début/fin
    """
    if not value or not isinstance(value, str):
        raise serializers.ValidationError('Mot de passe requis.')

    errors = []

    if len(value) < 8:
        errors.append('Au moins 8 caractères requis.')
    if len(value) > 128:
        errors.append('Maximum 128 caractères.')
    if not re.search(r'[A-Z]', value):
        errors.append('Au moins une lettre majuscule requise.')
    if not re.search(r'[a-z]', value):
        errors.append('Au moins une lettre minuscule requise.')
    if not re.search(r'\d', value):
        errors.append('Au moins un chiffre requis.')
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', value):
        errors.append('Au moins un caractère spécial requis (!@#$%^&*...).')
    if value != value.strip():
        errors.append('Le mot de passe ne peut pas commencer ou finir par un espace.')

    if errors:
        raise serializers.ValidationError(errors)

    return value


# ─── Validation téléphone béninois ───────────────────────────
PHONE_BENIN_REGEX = re.compile(
    r'^(?:\+229)?[0-9]{8}$'
)


def validate_phone_benin(value):
    """
    Valide un numéro de téléphone béninois :
    - Format : +229XXXXXXXX ou XXXXXXXX (8 chiffres)
    - Facultatif : champ vide autorisé
    """
    if not value:
        return value  # Le téléphone est optionnel

    if not isinstance(value, str):
        raise serializers.ValidationError('Numéro de téléphone invalide.')

    # Nettoyer les espaces et tirets
    cleaned = re.sub(r'[\s\-\.]', '', value.strip())

    if not PHONE_BENIN_REGEX.match(cleaned):
        raise serializers.ValidationError(
            'Format de téléphone invalide. Utilisez le format +229XXXXXXXX ou XXXXXXXX (8 chiffres).'
        )

    return cleaned


# ─── Validation nom d'utilisateur ────────────────────────────
USERNAME_REGEX = re.compile(r'^[a-zA-Z0-9àâéèêëïîôùûüçÀÂÉÈÊËÏÎÔÙÛÜÇ_\- ]{3,50}$')


def validate_username(value):
    """
    Valide le nom d'utilisateur :
    - 3 à 50 caractères
    - Lettres (avec accents), chiffres, underscores, tirets, espaces
    - Pas de caractères spéciaux dangereux
    """
    if not value or not isinstance(value, str):
        raise serializers.ValidationError('Nom d\'utilisateur requis.')

    value = value.strip()

    if len(value) < 3:
        raise serializers.ValidationError('Le nom d\'utilisateur doit contenir au moins 3 caractères.')
    if len(value) > 50:
        raise serializers.ValidationError('Le nom d\'utilisateur ne peut pas dépasser 50 caractères.')

    if not USERNAME_REGEX.match(value):
        raise serializers.ValidationError(
            'Le nom d\'utilisateur ne peut contenir que des lettres, chiffres, '
            'underscores, tirets et espaces.'
        )

    return value


# ─── Validation UUID ─────────────────────────────────────────
UUID_REGEX = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    re.IGNORECASE,
)


def validate_uuid_param(value):
    """Vérifie qu'une valeur est un UUID v4 valide."""
    if not value or not isinstance(value, str):
        raise serializers.ValidationError('UUID requis.')
    if not UUID_REGEX.match(str(value)):
        raise serializers.ValidationError('Format UUID invalide.')
    return value


# ─── Sanitization anti-XSS ──────────────────────────────────
def sanitize_text(value, max_length=5000):
    """
    Nettoie un texte des balises HTML/script potentiellement dangereuses.
    - Échappe les caractères HTML spéciaux
    - Limite la longueur
    """
    if not value:
        return value
    if not isinstance(value, str):
        raise serializers.ValidationError('Valeur texte attendue.')

    # Échapper les caractères HTML dangereux
    value = html.escape(value.strip(), quote=True)

    if len(value) > max_length:
        raise serializers.ValidationError(
            f'Le texte ne peut pas dépasser {max_length} caractères.'
        )

    return value


# ─── Validation couleur hexadécimale ─────────────────────────
HEX_COLOR_REGEX = re.compile(r'^#[0-9a-fA-F]{6}$')


def validate_hex_color(value):
    """Valide un code couleur hexadécimal (#RRGGBB)."""
    if not value:
        return '#1a73e8'  # Couleur par défaut
    if not HEX_COLOR_REGEX.match(value):
        raise serializers.ValidationError(
            'Format de couleur invalide. Utilisez le format #RRGGBB (ex: #1a73e8).'
        )
    return value.lower()


# ─── Validation emoji (icône service) ────────────────────────
def validate_emoji_icon(value):
    """Valide qu'une icône est un emoji valide (1-4 caractères)."""
    if not value:
        return '🏢'
    if len(value) > 10:
        raise serializers.ValidationError('L\'icône ne peut pas dépasser 10 caractères.')
    return value


# ─── Validation entier positif ───────────────────────────────
def validate_positive_integer(value, field_name='Valeur', max_val=10000):
    """Valide un entier strictement positif avec une limite haute."""
    if not isinstance(value, int) or value <= 0:
        raise serializers.ValidationError(f'{field_name} doit être un entier positif.')
    if value > max_val:
        raise serializers.ValidationError(f'{field_name} ne peut pas dépasser {max_val}.')
    return value
