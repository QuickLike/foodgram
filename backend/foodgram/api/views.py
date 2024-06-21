from django.shortcuts import render
from rest_framework import serializers, viewsets

from receipts.models import Ingredient, Receipt, Tag
from .serializers import IngredientSerializer, ReceiptSerializer, TagSerializer


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    http_method_names = ['get', ]


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    http_method_names = ['get', ]


class ReceiptViewSet(viewsets.ModelViewSet):
    queryset = Receipt.objects.all()
    serializer_class = ReceiptSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user,
        )


class ReceiptLinkViewSet(viewsets.ViewSet):
    pass


class DownloadShoppingCartViewSet(viewsets.ViewSet):
    pass


class SubscribeViewSet(viewsets.ModelViewSet):

    http_method_names = ['post', 'delete']
