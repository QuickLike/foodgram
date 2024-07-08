import csv
from datetime import datetime
from io import BytesIO

from django.contrib.auth import get_user_model
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import IngredientFilter, ReceiptFilter
from .paginations import LimitPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    FavouriteSerializer,
    IngredientSerializer,
    ReceiptSerializer,
    ReceiptCreateUpdateSerializer,
    ShoppingCartSerializer,
    TagSerializer,
    SubscribeSerializer,
    AvatarSerializer, SubscriptionsSerializer, UserSubscriberSerializer
)
from receipts.models import Favourite, Ingredient, IngredientReceipt, Receipt, ShoppingCart, Tag
from users.models import Subscription


User = get_user_model()


class IngredientTagMixin(viewsets.ModelViewSet):
    http_method_names = ('get',)
    pagination_class = None


class TagViewSet(IngredientTagMixin):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(IngredientTagMixin):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filterset_class = IngredientFilter
    filter_backends = (DjangoFilterBackend,)


class ReceiptViewSet(viewsets.ModelViewSet):
    pagination_class = LimitPagination
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
            return ReceiptCreateUpdateSerializer
        return ReceiptSerializer

    def __add_to(self, request, serializer, model, *args, **kwargs):
        user = request.user
        receipt = get_object_or_404(Receipt, pk=kwargs['pk'])

        if request.method == 'POST':
            serializer = serializer(
                data={'user': user.id, 'receipt': receipt.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            model_item = model.objects.filter(
                user=user,
                receipt=receipt
            )
            if not model_item.exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)  # Код ошибки должен быть 400, а не 404
            model_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post', 'delete'], detail=True, url_path='shopping_cart', permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, *args, **kwargs):
        return self.__add_to(request, ShoppingCartSerializer, ShoppingCart,  *args,  **kwargs)

    @action(methods=['post', 'delete'], detail=True, url_path='favorite', permission_classes=[IsAuthenticated])
    def favorite(self, request, *args, **kwargs):
        return self.__add_to(request, FavouriteSerializer, Favourite, *args, **kwargs)

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
        ings = (
            IngredientReceipt.objects.filter(
                receipt__shoppingcart__user=request.user
            )
        )
        shopping_list = [f"Список покупок {request.user.username}"]
        shopping_list.extend(
            f'{ing.ingredient.name}: {ing.amount} {ing.ingredient.measurement_unit}'
            for ing in ings
        )
        shopping_list = "\n".join(shopping_list)
        return FileResponse(
            BytesIO(shopping_list.encode('utf-8')),
            as_attachment=True,
            filename='shopping_list.txt'
        )


class UsersViewSet(UserViewSet):
    pagination_class = LimitPagination

    @action(methods=['get'], detail=False, url_path='me', permission_classes=[IsAuthenticated])
    def me(self, request, *args, **kwargs):
        return super().me(request, *args, **kwargs)

    @action(methods=['get'], detail=False, url_path='subscriptions', permission_classes=[IsAuthenticated])
    def subscriptions(self, request, *args, **kwargs):
        queryset = User.objects.filter(following__follower=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = UserSubscriberSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = UserSubscriberSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @action(methods=['post', 'delete'], detail=True, url_path='subscribe', permission_classes=[IsAuthenticated])
    def subscribe(self, request, *args, **kwargs):
        current_user = request.user
        user_to_subscribe = get_object_or_404(User, pk=kwargs['id'])

        if request.method == 'POST':
            if current_user == user_to_subscribe:
                return Response(
                    data={'detail': 'Нельзя подписаться на самого себя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            subscription, created = Subscription.objects.get_or_create(
                follower=current_user,
                following=user_to_subscribe
            )
            if not created:
                return Response(
                    data={'detail': 'Вы уже подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = SubscribeSerializer(
                subscription,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            subscription = Subscription.objects.filter(
                follower=current_user,
                following=user_to_subscribe
            ).first()
            if not subscription:
                return Response(
                    data={'detail': 'Вы не подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
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