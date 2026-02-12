from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
import os

def product_image_path(instance, filename):
    # Формат: media/products/game_<id>/product_<id>/filename.jpg
    return f'products/game_{instance.game.id}/product_{instance.id}/{filename}'

def game_logo_path(instance, filename):
    return f'games/logo/game_{instance.id}/{filename}'

class Game(models.Model):
    name = models.CharField(max_length=100)
    # Было: logo_url = models.URLField(...)
    logo = models.ImageField(
        upload_to=game_logo_path,
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])]
    )

    def __str__(self):
        return self.name

    @property
    def logo_url(self):
        """Совместимость со старым кодом — возвращает URL или None"""
        if self.logo:
            return self.logo.url
        return None


class Category(models.Model):
    name = models.CharField(max_length=100)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    old_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount = models.IntegerField(null=True, blank=True)
    # Было: image_url = models.URLField(...)
    image = models.ImageField(
        upload_to=product_image_path,
        blank=True,  # разрешает пустое значение в форме
        null=True,  # разрешает NULL в БД
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])],
        verbose_name="Изображение"
    )
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
        editable=False
    )
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    @property
    def image_url(self):
        """Возвращает URL изображения, если оно есть. Иначе — None."""
        if self.image:
            return self.image.url
        return None  # ←


class Basket(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Корзина пользователя {self.user.username}"

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now, verbose_name="дата заказа")
    status = models.CharField(max_length=50, default='pending')

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Дата отзыва")

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'product')  # Запрещает дублирование одного товара в вишлисте у одного пользователя
        verbose_name = "Wishlist item"
        verbose_name_plural = "Wishlist items"

    def __str__(self):
        return f"{self.user.username} — {self.product.name}"

def backup_path(instance, filename):
    return f"backups/{filename}"

class BackupFile(models.Model):
    file = models.FileField(upload_to=backup_path)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return os.path.basename(self.file.name)
    class Meta:
        verbose_name = "Бэкап"
        verbose_name_plural = "Бэкапы"