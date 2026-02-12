# api/views.py
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from main.models import Game, Category, Product, Review, Order
from .serializers import (
    GameSerializer, CategorySerializer, ProductSerializer,
    ReviewSerializer, OrderSerializer
)

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
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class OrderViewSet(viewsets.ReadOnlyModelViewSet):  # Только чтение!
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Order.objects.prefetch_related('items__product').all()
        return Order.objects.filter(user=self.request.user).prefetch_related('items__product')