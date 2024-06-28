import base64

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.generics import get_object_or_404

from receipts.models import Favourite, Ingredient, IngredientReceipt, Receipt, Tag
from users.serializers import UserSerializer


User = get_user_model()


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit'
        )


class ReceiptIngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class ReceiptSerializer(serializers.ModelSerializer):
    author = UserSerializer()
    ingredients = ReceiptIngredientSerializer(many=True)
    tags = TagSerializer(many=True)

    class Meta:
        model = Receipt
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )


class TokenSerializer(serializers.Serializer):
    email = serializers.CharField(required=True)
    password = serializers.CharField(required=True)


def validate(self, data):
    email = data.get('email')
    password = data.get('password')

    user = authenticate(email=email, password=password)
    if user is None:
        raise serializers.ValidationError('Неправильные учетные данные')

    return data


class FavouriteSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    receipt = serializers.PrimaryKeyRelatedField(
        queryset=Receipt.objects.all(),
    )

    class Meta:
        model = Favourite
        fields = ['id', 'user', 'receipt']
        read_only_fields = ['id']

    def create(self, validated_data):
        user = self.context['request'].user
        receipt = validated_data['receipt']
        return Favourite.objects.create(user=user, receipt=receipt)

    def validate(self, data):
        user = data['user']
        receipt = data['receipt']

        if Favourite.objects.filter(
                user=user,
                receipt=receipt
        ).exists():
            raise serializers.ValidationError("Рецепт уже добавлен в избранное")

        return data
