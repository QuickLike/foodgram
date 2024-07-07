from django.contrib.auth import get_user_model
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from .models import Subscription
from .paginations import LimitPagination
from .serializers import (
    UserCreateSerializer,
    UserSerializer,
    SubscribeSerializer,
    AvatarSerializer,
    SubscriptionsSerializer
)
from api.permissions import IsAuthorOrReadOnly

User = get_user_model()


class UserRegistrationView(UserViewSet):
    serializer_class = UserCreateSerializer
    queryset = User.objects.all()
    http_method_names = ['post', 'get']

    def create(self, request, *args, **kwargs):
        serializer = UserCreateSerializer(
            data=request.data, context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [AllowAny]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    @action(methods=['get'], detail=False)
    def me(self, request, *args, **kwargs):
        current_user = request.user
        serializer = self.get_serializer(current_user)
        return Response(serializer.data)

    @action(methods=['get'], detail=False)
    def subscriptions(self, request, *args, **kwargs):
        current_user = request.user
        subscriptions = current_user.subscriptions.all()
        recipes_limit = request.query_params.get('recipes_limit', None)
        context = self.get_serializer_context()
        context.update({'recipes_limit': recipes_limit, 'request': request})
        serializer = SubscriptionsSerializer(
            subscriptions,
            many=True,
            context=context
        )
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ['get']


class SubscribeViewSet(viewsets.ModelViewSet):
    serializer_class = SubscribeSerializer
    queryset = Subscription.objects.all()
    http_method_names = ['get', 'post', 'delete']
    permission_classes = [IsAuthenticated]
    pagination_class = LimitPagination

    def list(self, request, *args, **kwargs):
        current_user = request.user
        subscriptions = current_user.subscriptions.all()
        paginator = LimitPagination()
        page = paginator.paginate_queryset(subscriptions, request)
        serializer = SubscribeSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def create(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return Response(
                data={'detail': 'Необходимо авторизоваться.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        user_to_subscribe = get_object_or_404(User, pk=kwargs['user_id'])
        serializer = self.get_serializer(
            data={'user': user.id, 'subscribe_on': user_to_subscribe.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return Response(
                data={'detail': 'Необходимо авторизоваться.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        user_to_subscribe = get_object_or_404(User, pk=kwargs['user_id'])
        subscription = Subscription.objects.filter(
            user=user,
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
