from .models import Game, Basket, Wishlist
from django.contrib.auth.models import User


def call_pg_function(func_name, *args):
    """Вызов PostgreSQL-функции"""
    with connection.cursor() as cursor:
        placeholders = ', '.join(['%s'] * len(args))
        cursor.execute(f"SELECT {func_name}({placeholders})", args)
        return cursor.fetchone()[0]

def cart_and_wishlist_counts(request):
    basket_count = 0
    wishlist_count = 0
    if request.user.is_authenticated:
        try:
            basket_count = call_pg_function('get_basket_count', request.user.id)
            wishlist_count = call_pg_function('get_wishlist_count', request.user.id)
        except Exception:

            basket_count = Basket.objects.filter(user=request.user).count()
            wishlist_count = Wishlist.objects.filter(user=request.user).count()
    return {
        'basket_items_count': basket_count,
        'wishlist_count': wishlist_count,
    }

def games_context(request):
    """Добавляет список всех игр в контекст для навигации"""
    return {
        'games': Game.objects.all(),
    }


def games_context(request):
    """Добавляет список всех игр в контекст для навигации"""
    return {
        'games': Game.objects.all(),
    }