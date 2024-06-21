from rest_framework import serializers

from receipts.models import Ingredient, IngredientReceipt, Receipt, Tag


class IngredientReceiptSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(source='ingredient.measurement_unit', read_only=True)
    count = serializers.IntegerField(source='ingredientreceipt.count', read_only=True)

    class Meta:
        model = IngredientReceipt
        fields = ['name', 'measurement_unit', 'count']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


class ReceiptSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True,
        default=serializers.CurrentUserDefault()
    )
    ingredients = IngredientReceiptSerializer(
        source='ingredientreceipt_set',
        many=True,
        read_only=True
    )

    class Meta:
        model = Receipt
        fields = '__all__'
