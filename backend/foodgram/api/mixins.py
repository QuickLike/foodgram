from rest_framework import viewsets
from rest_framework.permissions import AllowAny


class IngredientTagMixin(viewsets.ModelViewSet):
    http_method_names = ('get',)
    pagination_class = None
