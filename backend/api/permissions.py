from rest_framework import permissions


class IsAuthorOrAdminOrReadOnly(permissions.IsAuthenticatedOrReadOnly):

    def has_object_permission(self, request, view, receipt):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_superuser
            or receipt.author == request.user
        )
