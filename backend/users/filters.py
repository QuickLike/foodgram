import django_filters


from .models import Subscribe


class SubscribeFilter(django_filters.FilterSet):
    recipes_limit = django_filters.NumberFilter(
        method='filter_recipes_limit',
        label='Количество рецептов',
    )

    class Meta:
        model = Subscribe
        fields = ['recipes_limit']

    def filter_recipes_limit(self, queryset, name, value):
        return queryset.filter(recipes_limit=value)
