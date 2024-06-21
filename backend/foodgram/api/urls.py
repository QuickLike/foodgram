from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from djoser.views import UserViewSet
from rest_framework.routers import DefaultRouter

from .views import DownloadShoppingCartViewSet, IngredientViewSet, ReceiptViewSet, ReceiptLinkViewSet, TagViewSet

router = DefaultRouter()
router.register('tags', TagViewSet)
router.register('ingredients', IngredientViewSet)
router.register('recipes', ReceiptViewSet)
router.register(r'recipes/(?P<receipt_id>\d+)/get-link)', ReceiptLinkViewSet, basename='receipt-link')
router.register('recipes/download_shopping_cart', DownloadShoppingCartViewSet, basename='download-shopping-cart')


urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('', include('djoser.urls.authtoken')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
