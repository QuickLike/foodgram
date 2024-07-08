from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('recipes', views.ReceiptViewSet, basename='recipes')
router.register('tags', views.TagViewSet, basename='tags')
router.register('ingredients', views.IngredientViewSet, basename='ingredients')
router.register('users', views.UsersViewSet, basename='users')


urlpatterns = [
    path('users/me/avatar/', views.AvatarView.as_view(), name='avatar'),
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
