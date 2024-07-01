from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
# router.register('users', UserViewSet)
router.register('recipes', views.ReceiptViewSet)
router.register('tags', views.TagViewSet)
router.register('ingredients', views.IngredientViewSet)
router.register(r'recipes/(?P<receipt_id>\d+)/get-link', views.ReceiptLinkViewSet, basename='receipt-link')
router.register(r'recipes/(?P<receipt_id>\d+)/favourite', views.FavouriteViewSet, basename='favourite')
router.register(r'recipes/(?P<receipt_id>\d+)/shopping_cart', views.ShoppingCartViewSet, basename='shopping-cart')
router.register('recipes/download_shopping_cart', views.DownloadShoppingCartViewSet, basename='download-shopping-cart')


urlpatterns = [
    path('users/me/avatar/', views.AvatarView.as_view(), name='avatar'),
    path('users/<int:user_id>/subscribe/', views.SubscribeViewSet.as_view({'post': 'create', 'delete': 'destroy'}), name='subscribe'),
    path('users/', views.UserRegistrationView.as_view({'post': 'create', 'get': 'list'}), name='user-registration'),
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )

# Пользователи
# GET      /api/users/               OK
# POST     /api/users/               90%
# GET      /api/users/{id}/          OK
# GET      /api/users/me/            OK
# PUT      /api/users/me/avatar/
# DELETE   /api/users/me/avatar/
# POST     /api/users/set_password/  OK
# POST     /api/auth/token/login/    OK
# POST     /api/auth/token/logout/   OK

# Теги
# GET      /api/tags/                OK
# GET      /api/tags/{id}/           OK

# Рецепты
# GET      /api/recipes/             OK
# POST     /api/recipes/
