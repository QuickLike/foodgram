import base64
import re

from django.contrib.auth.models import AnonymousUser
from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from .models import CustomUser, Subscription
from receipts.models import Receipt


class UserRecipesSerializer(serializers.ModelSerializer):

    class Meta:
        model = Receipt
        fields = ['id', 'name', 'image', 'cooking_time']


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class UserCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password'
        )
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        avatar = validated_data.pop('avatar', None)
        password = validated_data.pop('password')
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.save()
        if avatar is not None:
            user.avatar = avatar
            user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(
        required=False,
        allow_null=True
    )
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        request = self.context['request']
        if not request or not request.user.is_authenticated:
            return False
        user = request.user
        if isinstance(user, AnonymousUser):
            return False
        return Subscription.objects.filter(user=user, subscribe_on=obj).exists()


class UserSubscriberSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(
        required=False,
        allow_null=True
    )
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        request = self.context['request']
        if not request or not request.user.is_authenticated:
            return False
        user = request.user
        if isinstance(user, AnonymousUser):
            return False
        return Subscription.objects.filter(user=user, subscribe_on=obj).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        if request is None:
            return []

        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit is not None:
            try:
                recipes_limit = int(recipes_limit)
            except (TypeError, ValueError):
                recipes_limit = None

        if recipes_limit:
            return UserRecipesSerializer(obj.recipes.all()[:recipes_limit], many=True).data

        return UserRecipesSerializer(obj.recipes.all(), many=True).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class SubscribeSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Subscription
        fields = ('user', 'subscribe_on')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'subscribe_on'),
                message='Вы уже подписаны на этого пользователя.'
            ),
        ]

    def create(self, validated_data):
        user = validated_data['user']
        subscribe_on = validated_data['subscribe_on']
        if user == subscribe_on:
            raise serializers.ValidationError('Нельзя подписаться на самого себя.')

        subscription, created = Subscription.objects.get_or_create(
            user=user,
            subscribe_on=subscribe_on
        )
        if not created:
            raise serializers.ValidationError('Вы уже подписаны на этого пользователя.')
        return subscription

    def validate(self, data):
        user = data['user']
        subscribe_on = data['subscribe_on']

        if user == subscribe_on:
            raise serializers.ValidationError('Нельзя подписаться на самого себя.')

        if Subscription.objects.filter(user=user, subscribe_on=subscribe_on).exists():
            raise serializers.ValidationError('Вы уже подписаны на этого пользователя.')

        return data

    def to_representation(self, instance):
        user_to_subscribe = instance.subscribe_on
        return UserSubscriberSerializer(user_to_subscribe, context={'request': self.context.get('request')}).data


class SubscriptionsSerializer(serializers.ModelSerializer):
    subscriptions = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = ['subscriptions']

    def get_subscriptions(self, obj):
        request = self.context['request']
        user = request.user
        subscriptions = Subscription.objects.filter(user=user)
        return UserSubscriberSerializer(
            [subscription.subscribe_on for subscription in subscriptions],
            many=True,
            context={'request': request}
        ).data


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = CustomUser
        fields = ('avatar',)

    def update(self, instance, validated_data):
        avatar = validated_data.get('avatar')
        if avatar is None:
            raise serializers.ValidationError('Необходимо загрузить аватар.')
        instance.avatar = avatar
        instance.save()
        return instance
