from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from .filters import IngredientFilter, ReceiptFilter
from .mixins import IngredientTagMixin
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    FavouriteSerializer,
    IngredientSerializer,
    ReceiptSerializer,
    ReceiptCreateSerializer,
    ShoppingCartSerializer,
    TagSerializer
)
from receipts.models import Favourite, Ingredient, Receipt, ShoppingCart, Tag


User = get_user_model()


class TagViewSet(IngredientTagMixin):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(IngredientTagMixin):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filterset_class = IngredientFilter
    filter_backends = (DjangoFilterBackend,)


class ReceiptViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthorOrReadOnly, )
    queryset = Receipt.objects.all()
    serializer_class = ReceiptSerializer
    filterset_class = ReceiptFilter
    filter_backends = (DjangoFilterBackend,)
    http_method_names = ['get', 'post', 'patch', 'delete']

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user,
        )

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ReceiptCreateSerializer
        return ReceiptSerializer


class FavouriteViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthorOrReadOnly, IsAuthenticated)
    serializer_class = FavouriteSerializer
    http_method_names = ('post', 'delete')

    def create(self, request, *args, **kwargs):
        receipt = get_object_or_404(Receipt, pk=self.kwargs['receipt_id'])
        favourite_data = {'user': request.user.id, 'receipt': receipt.id}
        serializer = self.get_serializer(data=favourite_data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        receipt = get_object_or_404(Receipt, pk=self.kwargs['receipt_id'])
        favourite = Favourite.objects.get(user=request.user, receipt=receipt)
        if not favourite.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        favourite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ReceiptLinkViewSet(viewsets.ViewSet):
    pass


class ShoppingCartViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthorOrReadOnly, IsAuthenticated)
    http_method_names = ('post', 'delete')

    def create(self, request, *args, **kwargs):
        receipt = get_object_or_404(Receipt, pk=self.kwargs['receipt_id'])
        shopping_cart_data = {'user': request.user.id, 'receipt': receipt.id}
        serializer = ShoppingCartSerializer(data=shopping_cart_data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        receipt = get_object_or_404(Receipt, pk=self.kwargs['receipt_id'])
        shopping_cart_item = ShoppingCart.objects.get(user=request.user, receipt=receipt)
        if not shopping_cart_item.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        shopping_cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DownloadShoppingCartViewSet(viewsets.ViewSet):
    pass