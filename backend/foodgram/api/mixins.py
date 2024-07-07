from rest_framework import viewsets


class IngredientTagMixin(viewsets.ModelViewSet):
    http_method_names = ('get',)
    pagination_class = None
