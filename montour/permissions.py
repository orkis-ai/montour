# =============================================================
# MonTour — montour/permissions.py
# Permissions DRF personnalisées pour la RLS applicative
# =============================================================

from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    """
    Autorise uniquement les administrateurs (role='admin').
    Utilisé pour la gestion des services, utilisateurs, et stats globales.
    """
    message = 'Accès réservé aux administrateurs.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, 'role')
            and request.user.role == 'admin'
        )


class IsAgentOrAdmin(BasePermission):
    """
    Autorise les agents de service et les administrateurs.
    Utilisé pour appeler les tickets, marquer comme servi, etc.
    """
    message = 'Accès réservé aux agents et administrateurs.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, 'role')
            and request.user.role in ('agent', 'admin')
        )


class IsOwner(BasePermission):
    """
    RLS stricte : seul le propriétaire de l'objet peut y accéder.
    L'objet doit avoir un attribut `user` ou `user_id`.
    """
    message = 'Vous n\'êtes pas autorisé à accéder à cette ressource.'

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'user_id'):
            return obj.user_id == request.user.id
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return False


class IsOwnerOrAdmin(BasePermission):
    """
    RLS : le propriétaire de l'objet ou un administrateur.
    """
    message = 'Vous n\'êtes pas autorisé à accéder à cette ressource.'

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        if hasattr(obj, 'user_id'):
            return obj.user_id == request.user.id
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return False


class IsOwnerOrAgentOrAdmin(BasePermission):
    """
    RLS : le propriétaire, un agent ou un administrateur.
    Utilisé pour les actions sur les tickets.
    """
    message = 'Vous n\'êtes pas autorisé à accéder à cette ressource.'

    def has_object_permission(self, request, view, obj):
        if request.user.role in ('agent', 'admin'):
            return True
        if hasattr(obj, 'user_id'):
            return obj.user_id == request.user.id
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return False
