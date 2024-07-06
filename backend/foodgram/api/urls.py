from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views
from users.views import AvatarView, UserRegistrationView, SubscribeViewSet

router = DefaultRouter()
router.register('recipes', views.ReceiptViewSet)
router.register('tags', views.TagViewSet)
router.register('ingredients', views.IngredientViewSet)


urlpatterns = [
    path('users/me/avatar/', AvatarView.as_view(), name='avatar'),
    path('users/<int:user_id>/subscribe/', SubscribeViewSet.as_view({'post': 'create', 'delete': 'destroy'}), name='subscribe'),
    path('users/', UserRegistrationView.as_view({'post': 'create', 'get': 'list'}), name='user-registration'),
    path('users/me/', UserRegistrationView.as_view({'get': 'me'}), name='user-me'),
    path('users/subscriptions/', SubscribeViewSet.as_view({'get': 'list'}), name='subscriptions'),
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
