from django.contrib.auth import get_user_model
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from .serializers import UserCreateSerializer, UserSerializer, SubscribeSerializer
from .models import Subscription


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


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ['get']


class SubscribeViewSet(viewsets.ModelViewSet):
    http_method_names = ['post', 'delete']
    serializer_class = SubscribeSerializer

    def create(self, request, *args, **kwargs):
        user = request.user
        user_to_subscribe = get_object_or_404(User, pk=kwargs['user_id'])
        subscribe, create = Subscription.objects.create(user=user, subscribe_on=user_to_subscribe)
        print(create)
        return Response(status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        user_to_subscribe = get_object_or_404(User, pk=kwargs['user_id'])
        subscribe = Subscription.objects.get(user=request.user, subscribe_on=user_to_subscribe)
        print(subscribe)
        subscribe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
