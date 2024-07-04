import base64
from django.contrib.auth import authenticate, get_user_model
from django.core.files.base import ContentFile
from rest_framework import serializers, status

from receipts.models import Favourite, Ingredient, IngredientReceipt, Receipt, ShoppingCart, Tag
from users.serializers import UserSerializer, Base64ImageField

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
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(source='ingredient.measurement_unit')
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientReceipt
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )


class ReceiptIngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = IngredientReceipt
        fields = (
            'id',
            'amount'
        )


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class ReceiptSerializer(serializers.ModelSerializer):
    author = UserSerializer()
    ingredients = ReceiptIngredientSerializer(source='ingredientreceipt_set', many=True)
    tags = TagSerializer(many=True)
    is_in_shopping_cart = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()

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

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return ShoppingCart.objects.filter(user=request.user, receipt=obj).exists()

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Favourite.objects.filter(user=request.user, receipt=obj).exists()


class ReceiptCreateSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    ingredients = ReceiptIngredientCreateSerializer(many=True, required=True)
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    image = Base64ImageField(required=False)

    class Meta:
        model = Receipt
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
            'author',
        )

    def validate_ingredients(self, value):
        for ingredient_data in value:
            if not Ingredient.objects.filter(id=ingredient_data['id']).exists():
                raise serializers.ValidationError(f"Ingredient with ID {ingredient_data['id']} does not exist.")
        return value

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        receipt = Receipt.objects.create(**validated_data)

        receipt.tags.set(tags_data)

        for ingredient_data in ingredients_data:
            ingredient = Ingredient.objects.get(id=ingredient_data['id'])
            ingredient_receipt, created = IngredientReceipt.objects.get_or_create(
                receipt=receipt,
                ingredient=ingredient,
                defaults={'amount': ingredient_data['amount']}
            )
            if not created:
                ingredient_receipt.amount = ingredient_data['amount']
                ingredient_receipt.save()

        return receipt

    def to_representation(self, instance):
        return ReceiptSerializer(
            instance, context={'request': self.context.get('request')}).data


class FavouriteSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    receipt = serializers.PrimaryKeyRelatedField(queryset=Receipt.objects.all())

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

        if Favourite.objects.filter(user=user, receipt=receipt).exists():
            raise serializers.ValidationError(detail="Рецепт уже добавлен в избранное", code=status.HTTP_400_BAD_REQUEST)

        return data


class ShoppingCartSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    receipt = serializers.PrimaryKeyRelatedField(queryset=Receipt.objects.all())

    class Meta:
        model = ShoppingCart
        fields = ['id', 'user', 'receipt']
        read_only_fields = ['id']

    def create(self, validated_data):
        user = self.context['request'].user
        receipt = validated_data['receipt']
        return ShoppingCart.objects.create(user=user, receipt=receipt)

    def validate(self, data):
        user = data['user']
        receipt = data['receipt']

        if ShoppingCart.objects.filter(user=user, receipt=receipt).exists():
            raise serializers.ValidationError(detail="Рецепт уже добавлен в корзину", code=status.HTTP_400_BAD_REQUEST)

        return data
