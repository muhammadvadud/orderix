from rest_framework.permissions import BasePermission
from accounts.models import UserRoleChoices


class IsManager(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == UserRoleChoices.MANAGER


class IsWaiter(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == UserRoleChoices.WAITER


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == UserRoleChoices.ADMIN


class IsManagerOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in (
            UserRoleChoices.MANAGER, UserRoleChoices.ADMIN
        )
