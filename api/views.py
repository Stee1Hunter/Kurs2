# api/views.py
from rest_framework import viewsets, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from main.models import Game, Category, Product, Review, Order
from .serializers import (
    GameSerializer, CategorySerializer, ProductSerializer,
    ReviewSerializer, OrderSerializer
)

# === Пользовательские разрешения ===
class IsOwnerOrReadOnly(permissions.BasePermission):
    """Разрешает редактирование только автору"""
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return hasattr(obj, 'user') and obj.user == request.user

class IsOwnerOrStaff(permissions.BasePermission):
    """Разрешает редактирование владельцу или staff"""
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return (hasattr(obj, 'user') and obj.user == request.user) or request.user.is_staff

# === ViewSets ===
class GameViewSet(viewsets.ModelViewSet):
    queryset = Game.objects.all()
    serializer_class = GameSerializer
    permission_classes = [permissions.IsAdminUser]

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.select_related('game').all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAdminUser]

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('category', 'game').all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAdminUser]

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.select_related('product', 'user').all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrStaff]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Order.objects.prefetch_related('items__product').all()
        return Order.objects.filter(user=self.request.user).prefetch_related('items__product')

    def perform_create(self, serializer):
        # Запрещаем создание заказа через API
        raise serializers.ValidationError("Заказы создаются только через корзину.")

    def perform_update(self, serializer):
        # Только staff может менять статус
        if not self.request.user.is_staff:
            raise serializers.ValidationError("Только менеджер может изменять статус заказа.")
        serializer.save()

    def perform_destroy(self, instance):
        # Удалять может только админ или владелец (если статус 'pending')
        if not self.request.user.is_staff and instance.status != 'pending':
            raise serializers.ValidationError("Можно удалить только ожидающий заказ.")
        instance.delete()