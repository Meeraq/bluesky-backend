from rest_framework.permissions import BasePermission


class IsInRoles(BasePermission):
    def __init__(self, *roles):
        self.roles = roles

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        user_roles = request.user.profile.roles.values_list("name", flat=True)
        return any(role in user_roles for role in self.roles)

    def __call__(self):
        return self
