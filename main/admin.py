from django.contrib import admin
from django.contrib.auth.models import User
from .models import Game, Category, Product, Review, Basket, Order, OrderItem, Wishlist

@admin.register(BackupFile)
class BackupFileAdmin(ModelAdmin):
    list_display = ("file", "created_at")
    actions = ["restore_backup"]

    def has_add_permission(self, request):
        return False

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "make-backup/",
                self.admin_site.admin_view(self.make_backup_view),
                name="make_backup",
            ),
        ]
        return custom + urls

    def make_backup_view(self, request):
        try:
            media_backup_dir = os.path.join(settings.MEDIA_ROOT, 'backups')
            os.makedirs(media_backup_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"backup_{timestamp}.dump"
            abs_path = os.path.join(media_backup_dir, filename)

            db = settings.DATABASES["default"]

            # Передаём пароль через окружение — безопаснее
            env = os.environ.copy()
            env["PGPASSWORD"] = db["PASSWORD"]

            # Формируем аргументы без URL (избегаем подстановки пароля)
            cmd = [
                "pg_dump",
                "--host", db.get("HOST", "localhost"),
                "--port", str(db.get("PORT", "5432")),
                "--username", db["USER"],
                "--dbname", db["NAME"],
                "--format=custom",
                "--file", abs_path,
            ]

            result = subprocess.run(
                cmd,
                env=env,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            relative_path = f"backups/{filename}"

            # Сохраняем в модель
            backup = BackupFile(file=relative_path)
            backup.save()

            messages.success(request, "Бэкап успешно создан!")
            return redirect("admin:main_backupfile_changelist")

        except subprocess.CalledProcessError as e:
            messages.error(request, f"pg_dump failed: {e.stderr.strip()}")
        except Exception as e:
            messages.error(request, f"Ошибка: {e}")

        return redirect("admin:main_backupfile_changelist")

    def restore_backup(self, request, queryset):
        try:
            if queryset.count() != 1:
                self.message_user(request, "Выберите один бэкап!", messages.ERROR)
                return

            backup = queryset.first()
            backup_path = backup.file.path

            if not os.path.exists(backup_path):
                self.message_user(request, "Файл бэкапа не найден!", messages.ERROR)
                return

            db = settings.DATABASES["default"]
            db_url = (
                f"postgresql://{db['USER']}:{db['PASSWORD']}@"
                f"{db['HOST']}:{db['PORT']}/{db['NAME']}"
            )

            cmd = [
                "pg_restore",
                f"--dbname={db_url}",
                "--clean",
                "--if-exists",
                backup_path,
            ]

            subprocess.run(cmd, check=True)

            self.message_user(request, "База данных успешно восстановлена!", messages.SUCCESS)

        except subprocess.CalledProcessError:
            self.message_user(request, "Ошибка: pg_restore завершился неудачно.", messages.ERROR)

        except Exception as e:
            self.message_user(request, f"Ошибка восстановления: {e}", messages.ERROR)

    restore_backup.short_description = "Восстановить БД из выбранного бэкапа"

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('name', 'logo_preview')  # ← используем метод для превью
    search_fields = ('name',)
    list_filter = ('name',)

    # Добавляем метод для отображения превью логотипа в списке
    def logo_preview(self, obj):
        if obj.logo:
            return f'<img src="{obj.logo.url}" style="max-height: 30px;">'
        return "—"
    logo_preview.allow_tags = True
    logo_preview.short_description = "Логотип"

    fieldsets = (
        (None, {
            'fields': ('name', 'logo')  # ← теперь logo, а не logo_url
        }),
    )

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'game')
    search_fields = ('name', 'game__name')
    list_filter = ('game',)
    ordering = ('name',)
    fieldsets = (
        (None, {
            'fields': ('name', 'game')
        }),
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'game', 'price', 'discount', 'image_preview')

    # ...

    def image_preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" style="max-height: 30px;">'
        return "—"

    image_preview.allow_tags = True
    image_preview.short_description = "Изображение"

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'category', 'game')
        }),
        ('Цены', {
            'fields': ('price', 'old_price', 'discount')
        }),
        ('Изображение', {
            'fields': ('image',)  # ← не image_url!
        }),
    )

@admin.register(Basket)
class BasketAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'quantity', 'created_at')
    search_fields = ('user__username', 'product__name')
    list_filter = ('user', 'created_at')
    ordering = ('-created_at',)
    fieldsets = (
        ('Содержимое корзины', {
            'fields': ('user', 'product', 'quantity')
        }),
        ('Метаданные', {
            'fields': ('created_at',)
        }),
    )

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_price', 'status', 'created_at')
    search_fields = ('user__username', 'id')
    list_filter = ('status', 'created_at')
    ordering = ('-created_at',)
    fieldsets = (
        ('Информация о заказе', {
            'fields': ('user', 'total_price', 'status')
        }),
        ('Метаданные', {
            'fields': ('created_at',)
        }),
    )

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price')
    search_fields = ('order__id', 'product__name')
    list_filter = ('order', 'product')
    ordering = ('-order',)
    fieldsets = (
        ('Состав заказа', {
            'fields': ('order', 'product', 'quantity', 'price')
        }),
    )

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    search_fields = ('product__name', 'user__username')
    list_filter = ('rating', 'created_at')
    ordering = ('-created_at',)
    fieldsets = (
        ('Содержимое отзыва', {
            'fields': ('product', 'user', 'rating', 'comment')
        }),
        ('Метаданные', {
            'fields': ('created_at',)
        }),
    )

    @admin.register(Wishlist)
    class WishlistAdmin(admin.ModelAdmin):
        list_display = ('user', 'product', 'created_at')
        search_fields = ('user__username', 'product__name')
        list_filter = ('user', 'created_at')
        ordering = ('-created_at',)
        fieldsets = (
            ('Содержимое списка желаний', {
                'fields': ('user', 'product')
            }),
            ('Метаданные', {
                'fields': ('created_at',)
            }),
        )
