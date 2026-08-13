from rest_framework.permissions import BasePermission
from users.models import User

class IsTrainerOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in [User.Role.TRAINER, User.Role.ADMIN]
        )

class IsClient(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == User.Role.CLIENT
        )

class IsMembershipOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.role in [User.Role.TRAINER, User.Role.ADMIN]:
            return True
        return obj.client == request.user

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == User.Role.ADMIN
        )