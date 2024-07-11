from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.IsAuthenticatedOrReadOnly):

    def has_object_permission(self, request, view, receipt):
        return (
            request.method in permissions.SAFE_METHODS
            or receipt.author == request.user
        )
