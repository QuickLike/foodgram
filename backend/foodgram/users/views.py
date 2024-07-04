from django.contrib.auth import get_user_model
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from .serializers import UserCreateSerializer, UserSerializer, SubscribeSerializer, AvatarSerializer
from .models import Subscription
from api.permissions import IsAuthorOrReadOnly

User = get_user_model()


class UserRegistrationView(UserViewSet):
    serializer_class = UserCreateSerializer
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
        serializer = SubscribeSerializer(subscriptions, many=True)
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

    def list(self, request, *args, **kwargs):
        current_user = request.user
        subscriptions = current_user.user_subscriptions.all()
        serializer = SubscribeSerializer(subscriptions, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return Response(
                data={'detail': 'Authentication credentials were not provided.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        user_to_subscribe = get_object_or_404(User, pk=kwargs['user_id'])
        serializer = self.get_serializer(data={'user': user.id, 'subscribe_on': user_to_subscribe.id})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return Response(
                data={'detail': 'Authentication credentials were not provided.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        user_to_subscribe = get_object_or_404(User, pk=kwargs['user_id'])
        subscription = Subscription.objects.filter(user=user, subscribe_on=user_to_subscribe)
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