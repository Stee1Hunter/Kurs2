# api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GameViewSet, CategoryViewSet, ProductViewSet, ReviewViewSet, OrderViewSet

router = DefaultRouter()
router.register(r'games', GameViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'reviews', ReviewViewSet)
router.register(r'orders', OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),
]