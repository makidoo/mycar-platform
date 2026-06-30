from rest_framework import permissions
from .models import RoleUtilisateur


class AdminOnlyPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == RoleUtilisateur.ADMIN_SYS


class RoleBasedPermission(permissions.BasePermission):
    """
    Lecture : Police, Agent DGI, Superviseur DGI, Admin.
    Écriture : Agent DGI, Superviseur DGI, Admin.
    """
    ROLES_LECTURE = {
        RoleUtilisateur.POLICE,
        RoleUtilisateur.AGENT_DGI,
        RoleUtilisateur.SUP_DGI,
        RoleUtilisateur.ADMIN_SYS,
    }
    ROLES_ECRITURE = {
        RoleUtilisateur.AGENT_DGI,
        RoleUtilisateur.SUP_DGI,
        RoleUtilisateur.ADMIN_SYS,
    }

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return request.user.role in self.ROLES_LECTURE
        return request.user.role in self.ROLES_ECRITURE
