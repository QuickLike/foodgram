import django_filters


from .models import Subscribe


class SubscribeFilter(django_filters.FilterSet):
    recipes_limit = django_filters.NumberFilter(
        ...
    )

    class Meta:
        model = Subscribe
        fields = ['recipes_limit']
