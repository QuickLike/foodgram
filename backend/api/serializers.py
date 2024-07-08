from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers, status

from receipts.models import (
    Favourite, Ingredient, IngredientReceipt, Receipt, ShoppingCart, Tag
)
from users.models import CustomUser, Subscription

User = get_user_model()


class UserSerializer(DjoserUserSerializer):
    avatar = Base64ImageField(
        required=False,
        allow_null=True
    )
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = DjoserUserSerializer.Meta.fields + (
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, subscribe_on):
        request = self.context['request']
        if not request or not request.user.is_authenticated:
            return False
        user = request.user
        if isinstance(user, AnonymousUser):
            return False
        return Subscription.objects.filter(
            user=user,
            subscribe_on=subscribe_on
        ).exists()


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
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )
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
    ingredients = ReceiptIngredientSerializer(
        source='ingredientreceipt_set',
        many=True
    )
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
        return ShoppingCart.objects.filter(
            user=request.user,
            receipt=obj
        ).exists()

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Favourite.objects.filter(
            user=request.user,
            receipt=obj
        ).exists()


class ReceiptCreateSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    ingredients = ReceiptIngredientCreateSerializer(many=True, required=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True
    )
    image = Base64ImageField(required=True)

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
        if not value or value is None:
            raise serializers.ValidationError(
                detail="Обязательное поле 'ingredients'."
            )
        ingredients_ids = [ingredient_data['id'] for ingredient_data in value]
        if len(ingredients_ids) != len(set(ingredients_ids)):
            raise serializers.ValidationError(
                detail="Повторяющиеся Ингредиенты не допустимы."
            )
        for ingredient_id in ingredients_ids:
            if not Ingredient.objects.filter(id=ingredient_id).exists():
                raise serializers.ValidationError(
                    detail=f"Ингредиент с ID {ingredient_id} не существует."
                )
        return value

    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError("Обязательное поле 'tags'.")
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                detail="Повторяющиеся Теги не допустимы."
            )
        return tags

    def validate_image(self, image):
        if image is None:
            raise serializers.ValidationError({'image': 'Обязательное поле!'})
        return image

    def validate_cooking_time(self, value):
        if not value:
            raise serializers.ValidationError(
                detail="Обязательное поле 'cooking_time'."
            )
        return value

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        receipt = Receipt.objects.create(**validated_data)

        if 'cooking_time' not in validated_data:
            raise serializers.ValidationError(
                detail="Обязательное поле 'cooking_time'."
            )

        receipt.save()

        receipt.tags.set(tags_data)

        for ingredient_data in ingredients_data:
            ingredient = Ingredient.objects.get(id=ingredient_data['id'])
            ingr_receipt, created = IngredientReceipt.objects.get_or_create(
                receipt=receipt,
                ingredient=ingredient,
                defaults={'amount': ingredient_data['amount']}
            )
            if not created:
                ingr_receipt.amount = ingredient_data['amount']
                ingr_receipt.save()

        return receipt

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        tags = validated_data.pop('tags', None)

        if ingredients_data is None:
            raise serializers.ValidationError(
                detail="Обязательное поле 'ingredients'."
            )

        if tags is None:
            raise serializers.ValidationError(
                detail="Обязательное поле 'tags'."
            )

        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data['id']
            if not Ingredient.objects.filter(
                    id=ingredient_id
            ).exists():
                raise serializers.ValidationError(
                    detail=f"Ингредиент с ID {ingredient_id} не существует."
                )

        if tags is not None:
            instance.tags.set(tags)

        if ingredients_data is not None:
            instance.ingredientreceipt_set.all().delete()
            for ingredient_data in ingredients_data:
                IngredientReceipt.objects.create(
                    receipt=instance,
                    ingredient=Ingredient.objects.get(
                        id=ingredient_data['id']
                    ),
                    amount=ingredient_data['amount']
                )
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return ReceiptSerializer(
            instance, context={'request': self.context.get('request')}
        ).data


class FavouriteSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    receipt = serializers.PrimaryKeyRelatedField(
        queryset=Receipt.objects.all(),
        write_only=True
    )

    id = serializers.IntegerField(source='receipt.id', read_only=True)
    name = serializers.CharField(source='receipt.name', read_only=True)
    image = serializers.ImageField(source='receipt.image', read_only=True)
    cooking_time = serializers.IntegerField(
        source='receipt.cooking_time',
        read_only=True
    )

    class Meta:
        model = Favourite
        fields = ['id', 'name', 'image', 'cooking_time', 'user', 'receipt']
        read_only_fields = ['id']

    def create(self, validated_data):
        user = validated_data['user']
        receipt = validated_data['receipt']
        return Favourite.objects.create(user=user, receipt=receipt)

    def validate(self, data):
        user = data['user']
        receipt = data['receipt']

        if Favourite.objects.filter(user=user, receipt=receipt).exists():
            raise serializers.ValidationError(
                detail="Рецепт уже добавлен в избранное",
                code=status.HTTP_400_BAD_REQUEST
            )

        return data


class ShoppingCartSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    receipt = serializers.PrimaryKeyRelatedField(
        queryset=Receipt.objects.all(),
        write_only=True
    )

    id = serializers.IntegerField(source='receipt.id', read_only=True)
    name = serializers.CharField(source='receipt.name', read_only=True)
    image = serializers.ImageField(source='receipt.image', read_only=True)
    cooking_time = serializers.IntegerField(
        source='receipt.cooking_time',
        read_only=True
    )

    class Meta:
        model = ShoppingCart
        fields = ['id', 'name', 'image', 'cooking_time', 'user', 'receipt']
        read_only_fields = ['id']

    def create(self, validated_data):
        user = validated_data['user']
        receipt = validated_data['receipt']
        return ShoppingCart.objects.create(user=user, receipt=receipt)

    def validate(self, data):
        user = data['user']
        receipt = data['receipt']

        if ShoppingCart.objects.filter(user=user, receipt=receipt).exists():
            raise serializers.ValidationError(
                detail="Рецепт уже добавлен в корзину",
                code=status.HTTP_400_BAD_REQUEST
            )

        return data


class UserRecipesSerializer(serializers.ModelSerializer):

    class Meta:
        model = Receipt
        fields = ['id', 'name', 'image', 'cooking_time']


class UserSubscriberSerializer(UserSerializer):
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = UserSerializer.Meta.fields + (
            'recipes',
            'recipes_count',
        )

    def get_recipes(self, user):
        request = self.context.get('request')
        if request is None:
            return []

        recipes_limit = int(request.GET.get('recipes_limit', 10**10))

        return UserRecipesSerializer(user.recipes.all()[:recipes_limit], many=True).data

    def get_recipes_count(self, user):
        return user.recipes.count()


class SubscribeSerializer(serializers.ModelSerializer):
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

    def to_representation(self, instance):
        user_to_subscribe = instance.subscribe_on
        return UserSubscriberSerializer(
            user_to_subscribe,
            context={'request': self.context.get('request')}
        ).data


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
