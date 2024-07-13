from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from receipts.models import (
    Favourite,
    Ingredient,
    IngredientInReceipt,
    Receipt,
    ShoppingCart,
    Subscription,
    Tag
)

User = get_user_model()


class UserSerializer(DjoserUserSerializer):
    avatar = Base64ImageField(
        required=False,
        allow_null=True
    )
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            *DjoserUserSerializer.Meta.fields,
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, author):
        request = self.context['request']
        if not request or not request.user.is_authenticated:
            return False
        user = request.user
        return Subscription.objects.filter(
            follower=user,
            author=author
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
        model = IngredientInReceipt
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = IngredientInReceipt
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
        source='ingredients_in_receipts',
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

    def get_is_in_shopping_cart(self, receipt):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return ShoppingCart.objects.filter(
            user=request.user,
            receipt=receipt
        ).exists()

    def get_is_favorited(self, receipt):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Favourite.objects.filter(
            user=request.user,
            receipt=receipt
        ).exists()


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(default=serializers.CurrentUserDefault())
    ingredients = RecipeIngredientSerializer(many=True, required=True)
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

    def validate(self, data):
        fields = ('tags', 'ingredients')
        for field in fields:
            if field not in data:
                raise serializers.ValidationError(
                    f"Обязательное поле '{field}'."
                )
        return data

    def validate_ingredients(self, ingredients):
        return self.validate_items(
            ([ingredient['id'] for ingredient in ingredients], ingredients),
            'ingredients',
            Ingredient)

    def validate_tags(self, tags):
        return self.validate_items(
            ([tag.id for tag in tags], tags),
            'tags',
            Tag
        )

    def validate_image(self, image):
        if not image:
            raise serializers.ValidationError(
                'Обязательное поле "image".'
            )
        return image

    def validate_cooking_time(self, cooking_time):
        if not cooking_time:
            raise serializers.ValidationError(
                'Обязательное поле "cooking_time".'
            )
        return cooking_time

    @staticmethod
    def validate_items(items, field_name, model):
        if not items[1]:
            raise serializers.ValidationError(
                f'{field_name}: Обязательное поле!'
            )

        invalid_items = [
            item for item in items[0] if not model.objects.filter(
                id=item
            ).exists()
        ]
        if invalid_items:
            raise serializers.ValidationError(
                {field_name: f'Элементов с ID {invalid_items} не существует.'}
            )

        duplicates = [item for item in items[1] if items[1].count(item) > 1]
        if duplicates:
            raise serializers.ValidationError(
                {field_name: 'Повторяющиеся элементы не допустимы.\n'
                             f'{duplicates}'}
            )

        return items[1]

    @staticmethod
    def ingredients_receipts_create(ingredients, receipt):
        IngredientInReceipt.objects.bulk_create(
            IngredientInReceipt(
                receipt=receipt,
                ingredient=Ingredient.objects.get(id=ingredient['id']),
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        )

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        receipt = Receipt.objects.create(**validated_data)
        receipt.save()
        receipt.tags.set(tags_data)
        self.ingredients_receipts_create(ingredients_data, receipt)
        return receipt

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance.tags.set(tags)
        instance.ingredients_in_receipts.all().delete()
        self.ingredients_receipts_create(ingredients_data, instance)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return ReceiptSerializer(
            instance, context={'request': self.context.get('request')}
        ).data


class UserRecipesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipt
        fields = ['id', 'name', 'image', 'cooking_time']


class UserSubscriberSerializer(UserSerializer):
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            *UserSerializer.Meta.fields,
            'recipes',
            'recipes_count',
        )

    def get_recipes(self, user):
        request = self.context.get('request')
        limit = int(request.GET.get('recipes_limit', 10 ** 10))
        recipes = user.recipes.all()[:limit]
        return UserRecipesSerializer(recipes, many=True).data

    def get_recipes_count(self, user):
        return user.recipes.count()


class SubscriptionsSerializer(serializers.ModelSerializer):
    subscriptions = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = ['subscriptions']

    def get_subscriptions(self, obj):
        request = self.context['request']
        user = request.user
        subscriptions = Subscription.objects.filter(follower=user)
        return UserSubscriberSerializer(
            [subscription.following for subscription in subscriptions],
            many=True,
            context={'request': request}
        ).data


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)

    def update(self, instance, validated_data):
        avatar = validated_data.get('avatar')
        if avatar is None:
            raise serializers.ValidationError('Необходимо загрузить аватар.')
        instance.avatar = avatar
        instance.save()
        return instance
