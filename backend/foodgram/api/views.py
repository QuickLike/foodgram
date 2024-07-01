from django.contrib.auth import get_user_model
from django.shortcuts import render, get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from djoser.views import UserViewSet as DjoserUserViewSet
from djoser.compat import get_user_email
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status, viewsets, views, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework.response import Response

from .mixins import IngredientTagMixin
from .permissions import IsAuthorOrReadOnly
from .serializers import FavouriteSerializer, IngredientSerializer, ReceiptSerializer, ShoppingCartSerializer, TagSerializer, TokenSerializer
from receipts.models import Favourite, Ingredient, Receipt, ShoppingCart, Subscription, Tag
from users.serializers import UserCreateSerializer, UserSerializer


User = get_user_model()


class AvatarView(APIView):
    permission_classes = (IsAuthorOrReadOnly,)

    def put(self, request,  *args,  **kwargs):
        serializer = UserSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        user = request.user
        user.avatar = None
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(IngredientTagMixin):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(IngredientTagMixin):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class ReceiptViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthorOrReadOnly,)
    queryset = Receipt.objects.all()
    serializer_class = ReceiptSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('is_in_shopping_cart', 'is_favorited', 'tags__slug', 'author__id')
    http_method_names = ['get', 'post', 'patch', 'delete']

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user,
        )


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
    serializer_class = ShoppingCartSerializer
    http_method_names = ('post', 'delete')

    def create(self, request, *args, **kwargs):
        receipt = get_object_or_404(Receipt, pk=self.kwargs['receipt_id'])
        shopping_cart_data = {'user': request.user.id, 'receipt': receipt.id}
        serializer = self.get_serializer(data=shopping_cart_data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
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


class SubscribeViewSet(viewsets.ModelViewSet):
    http_method_names = ['post', 'delete']

    def create(self, request, *args, **kwargs):
        user = request.user
        user_to_subscribe = get_object_or_404(User, pk=kwargs['user_id'])
        subscribe, create = Subscription.objects.create(user=user, subscribe_to=user_to_subscribe)
        return Response(status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        user = request.user
        user_to_subscribe = User.objects.get(pk=kwargs['user_id'])
        if not user_to_subscribe.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        subscribe = Subscription.objects.get(user=user, subscribe_to=user_to_subscribe)
        subscribe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TokenLoginView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = TokenSerializer

    @method_decorator(csrf_exempt)
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = get_object_or_404(User, email=email)
        token = str(AccessToken.for_user(user))
        return Response({'auth_token': token}, status=status.HTTP_200_OK)


class TokenLogoutView(views.APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TokenSerializer

    def post(self, request):
        try:
            tokens = OutstandingToken.objects.filter(user=request.user)
            for token in tokens:
                token.delete()
            return Response({"detail": "Токен успешно удален"}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"detail": 'Произошла ошибка при удалении токена'}, status=status.HTTP_400_BAD_REQUEST)


class UserMeView(views.APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request,  *args,  **kwargs):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)


# class UserRegistrationView(APIView):
#     permission_classes = (AllowAny,)
#     queryset = User.objects.all()
#     serializer_class = UserCreateSerializer
#
#     def post(self, request, *args, **kwargs):
#         serializer = UserCreateSerializer(data=request.data, context={'request': request})
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserRegistrationView(viewsets.ModelViewSet):
    serializer_class = UserCreateSerializer
    permission_classes = (AllowAny,)
    queryset = User.objects.all()
    http_method_names = ['post', 'get']

    def create(self, request, *args, **kwargs):
        serializer = UserCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ['get']
    permission_classes = (AllowAny,)
