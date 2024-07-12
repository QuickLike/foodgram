from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import IngredientFilter, ReceiptFilter
from .paginations import LimitPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    IngredientSerializer,
    ReceiptSerializer,
    RecipeSerializer,
    TagSerializer,
    AvatarSerializer,
    UserSubscriberSerializer,
    UserRecipesSerializer
)
from .utils import generate_shopping_list
from receipts.models import (
    Favourite,
    Ingredient,
    Receipt,
    ShoppingCart,
    Subscription,
    Tag
)

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
            return RecipeSerializer
        return ReceiptSerializer

    def _shopping_cart_or_favorite(self, request, model, **kwargs):
        user = request.user
        receipt = get_object_or_404(Receipt, pk=kwargs['pk'])

        if request.method == 'POST':
            item, is_created = model.objects.get_or_create(
                user=user,
                receipt=receipt
            )
            if not is_created:
                raise ValidationError(
                    'Рецепт уже добавлен!'
                )
            serializer = UserRecipesSerializer(receipt)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        get_object_or_404(model, user=user, receipt=receipt).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['post', 'delete'],
        detail=True,
        url_path='shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, **kwargs):
        return self._shopping_cart_or_favorite(
            request,
            ShoppingCart,
            **kwargs
        )

    @action(
        methods=['post', 'delete'],
        detail=True,
        url_path='favorite',
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, **kwargs):
        return self._shopping_cart_or_favorite(
            request,
            Favourite,
            **kwargs
        )

    @action(methods=['get'], detail=True, url_path='get-link')
    def get_link(self, request, **kwargs):
        get_object_or_404(Receipt, pk=kwargs['pk'])
        full_link = request.build_absolute_uri(
            f'/s/{kwargs["pk"]}'
        )
        return Response(
            data={'short-link': full_link},
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=False, url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        return FileResponse(
            generate_shopping_list(request.user),
            filename='shopping_list.txt',
            content_type='text/plain; charset=utf-8'
        )


class UsersViewSet(UserViewSet):
    pagination_class = LimitPagination

    def get_permissions(self):
        if self.action == settings.RESERVED_USERNAME:
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(
        methods=['get'],
        detail=False,
        url_path='subscriptions',
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        queryset = User.objects.filter(authors__follower=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = UserSubscriberSerializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = UserSubscriberSerializer(
            queryset,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)

    @action(
        methods=['post', 'delete'],
        detail=True,
        url_path='subscribe',
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, **kwargs):
        author = get_object_or_404(User, pk=kwargs['id'])

        if request.method == 'POST':
            if request.user == author:
                raise ValidationError(
                    {'detail': 'Нельзя подписаться на самого себя.'}
                )

            subscription, created = Subscription.objects.get_or_create(
                follower=request.user,
                author=author
            )
            if not created:
                raise ValidationError(
                    {'detail': 'Вы уже подписаны на этого пользователя.'}
                )

            serializer = UserSubscriberSerializer(
                author,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        get_object_or_404(
            Subscription,
            follower=request.user,
            author=author
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AvatarView(APIView):
    permission_classes = (IsAuthorOrReadOnly,)

    def put(self, request):
        user = request.user
        serializer = AvatarSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request):
        user = request.user
        user.avatar = None
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
