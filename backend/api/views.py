import csv

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import IngredientFilter, ReceiptFilter
from .mixins import IngredientTagMixin
from .paginations import LimitPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    FavouriteSerializer,
    IngredientSerializer,
    ReceiptSerializer,
    ReceiptCreateSerializer,
    ShoppingCartSerializer,
    TagSerializer, UserCreateSerializer, UserSerializer, SubscriptionsSerializer, SubscribeSerializer, AvatarSerializer
)
from receipts.models import Favourite, Ingredient, Receipt, ShoppingCart, Tag
from users.models import Subscription

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
    permission_classes = (IsAuthorOrReadOnly,)
    queryset = Receipt.objects.all()
    serializer_class = ReceiptSerializer
    filterset_class = ReceiptFilter
    filter_backends = (DjangoFilterBackend,)
    http_method_names = ['get', 'post', 'patch', 'delete']
    lookup_field = 'pk'

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user,
        )

    def get_serializer_class(self):
        if self.request.method not in SAFE_METHODS:
            return ReceiptCreateSerializer
        return ReceiptSerializer

    @action(methods=['post', 'delete'], detail=True, url_path='shopping_cart')
    def shopping_cart(self, request, *args, **kwargs):
        user = request.user
        receipt = get_object_or_404(Receipt, pk=kwargs['pk'])

        if not user.is_authenticated:
            return Response(
                data={'detail': 'Необходимо авторизоваться.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if request.method == 'POST':
            serializer = ShoppingCartSerializer(
                data={'user': user.id, 'receipt': receipt.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            shopping_cart_item = ShoppingCart.objects.filter(
                user=user,
                receipt=receipt
            )
            if not shopping_cart_item.exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            shopping_cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post', 'delete'], detail=True, url_path='favorite')
    def favorite(self, request, *args, **kwargs):
        user = request.user
        receipt = get_object_or_404(Receipt, pk=kwargs['pk'])

        if not user.is_authenticated:
            return Response(
                data={'detail': 'Необходимо авторизоваться.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if request.method == 'POST':
            serializer = FavouriteSerializer(
                data={'user': user.id, 'receipt': receipt.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            favourite = Favourite.objects.filter(user=user, receipt=receipt)
            if not favourite.exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            favourite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['get'], detail=True, url_path='get-link')
    def get_link(self, request, *args, **kwargs):
        receipt = Receipt.objects.get(pk=kwargs['pk'])
        full_link = f'https://{request.get_host()}/s/{receipt.short_link}'
        return Response(
            data={'short-link': full_link},
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=False, url_path='download_shopping_cart')
    def download_shopping_cart(self, request, *args, **kwargs):
        shopping_cart = [
            item.receipt for item in ShoppingCart.objects.filter(
                user=request.user
            )
        ]
        response = Response(content_type='text/csv')
        long_line = 'attachment; filename="shopping_cart.csv"'
        response['Content-Disposition'] = long_line

        writer = csv.writer(response)
        writer.writerow(
            [
                'Название',
                'Изображение',
                'Описание',
                'Ингредиенты',
                'Теги',
                'Время приготовления',
                'Опубликовано',
                'Ссылка'
            ]
        )

        for item in shopping_cart:
            writer.writerow([
                item.name,
                item.image,
                item.text,
                item.ingredients,
                item.tags,
                item.cooking_time,
                item.published_at,
                item.short_link,
            ])

        return response


class UsersViewSet(UserViewSet):

    @action(methods=['get'], detail=False, url_path='me', permission_classes=[IsAuthenticated])
    def me(self, request, *args, **kwargs):
        return super().me(request, *args, **kwargs)

    @action(methods=['get'], detail=False, url_path='subscriptions', permission_classes=[IsAuthenticated])
    def subscriptions(self, request, *args, **kwargs):
        subscriptions = request.user.subscriptions.all()
        paginator = LimitPagination()
        page = paginator.paginate_queryset(subscriptions, request)
        serializer = SubscribeSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @action(methods=['post', 'delete'], detail=True, url_path='subscribe', permission_classes=[IsAuthenticated])
    def subscribe(self, request, *args, **kwargs):
        current_user = request.user
        if request.method == 'POST':
            if not current_user.is_authenticated:
                return Response(
                    data={'detail': 'Необходимо авторизоваться.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            user_to_subscribe = get_object_or_404(User, pk=kwargs['id'])
            serializer = SubscribeSerializer(
                data={'user': current_user.id, 'subscribe_on': user_to_subscribe.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        else:

            if not current_user.is_authenticated:
                return Response(
                    data={'detail': 'Необходимо авторизоваться.'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            user_to_subscribe = get_object_or_404(User, pk=kwargs['id'])
            subscription = Subscription.objects.filter(
                user=current_user,
                subscribe_on=user_to_subscribe
            )
            if not subscription:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class AvatarView(APIView):
    permission_classes = (IsAuthorOrReadOnly,)

    def put(self, request, *args, **kwargs):
        user = request.user
        serializer = AvatarSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        user = request.user
        user.avatar = None
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)