# main/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.views import View
from django.http import JsonResponse
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import Game, Category, Product, User, Basket, Order, OrderItem, Review, Wishlist
from .forms import ProfileUpdateForm, GameForm, ProductForm, CategoryForm, UserForm, OrderForm, ReviewForm, LoginForm, RegistrationForm
from django.core.paginator import Paginator
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
import logging

logger = logging.getLogger(__name__)


# --- Вспомогательные функции для вызова PostgreSQL ---
def call_pg_function(func_name, *args):
    from django.db import connection
    with connection.cursor() as cursor:
        placeholders = ', '.join(['%s'] * len(args))
        cursor.execute(f"SELECT {func_name}({placeholders})", args)
        return cursor.fetchone()[0]


def call_pg_procedure(proc_name, *args):
    from django.db import connection
    with connection.cursor() as cursor:
        placeholders = ', '.join(['%s'] * len(args))
        cursor.execute(f"CALL {proc_name}({placeholders})", args)


# --- Views ---
class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'main/order_detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


class UserOrdersView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'main/myorders.html'
    context_object_name = 'orders'
    paginate_by = 10

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')


def login_user(request):
    if request.method == "POST":
        form = LoginForm(data=request.POST)  # ← Используем вашу кастомную форму
        if form.is_valid():
            login(request, form.get_user())
            next_url = request.GET.get('next')
            return redirect(next_url or 'index')  # ← Лучше использовать name URL
    else:
        form = LoginForm()  # ← Не AuthenticationForm!
    return render(request, 'main/login.html', {'form': form})


def registration_user(request):
    if request.method == "POST":
        form = RegistrationForm(data=request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            next_url = request.GET.get('next')
            return redirect(next_url or 'index')  # ← Используем name URL
    else:
        form = RegistrationForm()
    return render(request, 'main/register.html', {'form': form})

def logout_user(request):
    logout(request)
    return redirect('/')


@login_required
def profile_view(request):
    basket_count = call_pg_function('get_basket_count', request.user.id)
    wishlist_count = call_pg_function('get_wishlist_count', request.user.id)
    return render(request, 'main/profile.html', {
        'basket_items_count': basket_count,
        'wishlist_count': wishlist_count,
    })


# --- Админка: CRUD ---
@method_decorator(staff_member_required, name='dispatch')
class ProductCreateView(CreateView):
    form_class = ProductForm
    template_name = 'main/product_form.html'
    success_url = reverse_lazy('index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Добавить товар'
        return context


@method_decorator(staff_member_required, name='dispatch')
class ProductUpdateView(UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'main/product_form.html'
    success_url = reverse_lazy('index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Редактировать: {self.object.name}'
        return context

    # При обновлении через форму — триггер сам обработает скидку
    # Но если вы хотите использовать процедуру — можно добавить логику в form_valid


@method_decorator(staff_member_required, name='dispatch')
class ProductDeleteView(DeleteView):
    model = Product
    template_name = 'main/product_confirm_delete.html'
    success_url = reverse_lazy('index')

    def delete(self, request, *args, **kwargs):
        # Сначала удаляем сам товар (родительский метод)
        response = super().delete(request, *args, **kwargs)

        # Затем вызываем процедуру очистки "битых" записей
        try:
            call_pg_procedure('cleanup_orphaned_items')
        except Exception as e:
            # Логируем ошибку, но не прерываем удаление
            logger.error(f"Ошибка при очистке после удаления товара: {e}")

        return response
@method_decorator(staff_member_required, name='dispatch')
class GameCreateView(CreateView):
    model = Game
    form_class = GameForm
    template_name = 'main/game_form.html'
    success_url = reverse_lazy('index')


@method_decorator(staff_member_required, name='dispatch')
class GameUpdateView(UpdateView):
    model = Game
    form_class = GameForm
    template_name = 'main/game_form.html'
    success_url = reverse_lazy('index')


@method_decorator(staff_member_required, name='dispatch')
class GameDeleteView(DeleteView):
    model = Game
    template_name = 'main/game_confirm_delete.html'
    success_url = reverse_lazy('index')


# Категории
@method_decorator(staff_member_required, name='dispatch')
class CategoryCreateView(CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'main/category_form.html'
    success_url = reverse_lazy('index')


@method_decorator(staff_member_required, name='dispatch')
class CategoryUpdateView(UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'main/category_form.html'
    success_url = reverse_lazy('index')


@method_decorator(staff_member_required, name='dispatch')
class CategoryDeleteView(DeleteView):
    model = Category
    template_name = 'main/category_confirm_delete.html'
    success_url = reverse_lazy('index')


# Пользователи
@method_decorator(staff_member_required, name='dispatch')
class UserCreateView(CreateView):
    model = User
    form_class = UserForm
    template_name = 'main/user_form.html'
    success_url = reverse_lazy('index')


@method_decorator(staff_member_required, name='dispatch')
class UserUpdateView(UpdateView):
    model = User
    form_class = UserForm
    template_name = 'main/user_form.html'
    success_url = reverse_lazy('index')


@method_decorator(staff_member_required, name='dispatch')
class UserDeleteView(DeleteView):
    model = User
    template_name = 'main/user_confirm_delete.html'
    success_url = reverse_lazy('index')


# Заказы
@method_decorator(staff_member_required, name='dispatch')
class OrderListView(ListView):
    model = Order
    template_name = 'main/order_list.html'
    context_object_name = 'orders'


@method_decorator(staff_member_required, name='dispatch')
class OrderDetailView(DetailView):
    model = Order
    template_name = 'main/order_detail.html'


@method_decorator(staff_member_required, name='dispatch')
class OrderUpdateView(UpdateView):
    model = Order
    form_class = OrderForm
    template_name = 'main/order_form.html'
    success_url = reverse_lazy('order_list')


# Отзывы
class ReviewListView(ListView):
    model = Review
    template_name = 'main/review_list.html'
    context_object_name = 'reviews'


@method_decorator(staff_member_required, name='dispatch')
class ReviewUpdateView(UpdateView):
    model = Review
    form_class = ReviewForm
    template_name = 'main/review_form.html'
    success_url = reverse_lazy('review_list')


@method_decorator(staff_member_required, name='dispatch')
class ReviewDeleteView(DeleteView):
    model = Review
    template_name = 'main/review_confirm_delete.html'
    success_url = reverse_lazy('review_list')


# IndexView
class IndexView(View):
    def get(self, request):
        games = Game.objects.all()
        games_with_discounts = []

        for game in games:
            discounted_products = game.product_set.filter(discount__isnull=False)[:4]
            if discounted_products:
                games_with_discounts.append({
                    'game': game,
                    'products': discounted_products
                })

        basket_count = call_pg_function('get_basket_count', request.user.id) if request.user.is_authenticated else 0
        return render(request, 'main/index.html', {
            'games': games,
            'games_with_discounts': games_with_discounts,
            'basket_items_count': basket_count,
        })


# ProductView
class ProductView(View):
    def get(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        reviews = Review.objects.filter(product=product)
        similar_products = Product.objects.filter(
            category=product.category
        ).exclude(id=product.id)[:4]

        in_wishlist = False
        if request.user.is_authenticated:
            in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()

        basket_count = call_pg_function('get_basket_count', request.user.id) if request.user.is_authenticated else 0
        return render(request, 'main/prodinfo.html', {
            'product': product,
            'reviews': reviews,
            'similar_products': similar_products,
            'in_wishlist': in_wishlist,
            'basket_items_count': basket_count,
        })


# AboutView
class AboutView(View):
    def get(self, request):
        basket_count = call_pg_function('get_basket_count', request.user.id) if request.user.is_authenticated else 0
        return render(request, 'main/about.html', {
            'basket_items_count': basket_count,
        })


# BasketView
class BasketView(LoginRequiredMixin, View):
    def get(self, request):
        basket_items = Basket.objects.filter(user=request.user)
        total = call_pg_function('get_basket_total', request.user.id)
        count = call_pg_function('get_basket_count', request.user.id)

        return render(request, 'main/basket.html', {
            'basket_items': basket_items,
            'total': total,
            'basket_items_count': count,
        })


# AddToBasketView
class AddToBasketView(LoginRequiredMixin, View):
    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        basket_item, created = Basket.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={'quantity': 1}
        )
        if not created:
            basket_item.quantity += 1
            basket_item.save()

        new_count = call_pg_function('get_basket_count', request.user.id)
        return JsonResponse({'success': True, 'basket_items_count': new_count})


# RemoveFromBasketView
class RemoveFromBasketView(LoginRequiredMixin, View):
    def post(self, request, item_id):
        basket_item = get_object_or_404(Basket, id=item_id, user=request.user)
        basket_item.delete()
        new_count = call_pg_function('get_basket_count', request.user.id)
        return JsonResponse({'success': True, 'basket_items_count': new_count})


# UpdateBasketView
class UpdateBasketView(LoginRequiredMixin, View):
    def post(self, request, item_id):
        try:
            quantity = int(request.POST.get('quantity', 1))
            if quantity < 1:
                raise ValueError
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'message': 'Invalid quantity'})

        basket_item = get_object_or_404(Basket, id=item_id, user=request.user)
        basket_item.quantity = quantity
        basket_item.save()
        return JsonResponse({'success': True})


# CreateOrderView — используем процедуру
class CreateOrderView(LoginRequiredMixin, View):
    def post(self, request):
        basket_count = call_pg_function('get_basket_count', request.user.id)
        if basket_count == 0:
            return JsonResponse({'success': False, 'message': 'Корзина пуста'}, status=400)

        try:
            call_pg_procedure('create_order_from_basket', request.user.id)

            return redirect('my_orders')
        except Exception as e:
            logger.error(f"Ошибка при создании заказа: {e}")
            return JsonResponse({'success': False, 'message': 'Ошибка при создании заказа'}, status=500)

# AddReviewView — триггер сам проверит покупку
class AddReviewView(LoginRequiredMixin, View):
    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)

        try:
            rating = int(request.POST.get('rating', 0))
            if rating < 1 or rating > 5:
                raise ValueError
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'message': 'Invalid rating'})

        comment = request.POST.get('comment', '').strip()
        if not comment:
            return JsonResponse({'success': False, 'message': 'Comment cannot be empty'})

        try:
            Review.objects.create(
                product=product,
                user=request.user,
                rating=rating,
                comment=comment
            )
            # ← Добавьте эту строку:
            call_pg_procedure('recalculate_product_ratings')
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})


# catalog_view
def catalog_view(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    categories = Category.objects.filter(game=game)
    products = Product.objects.filter(game=game)

    params = request.GET.copy()
    selected_categories = params.getlist('category', [])
    min_price = params.get('min_price', '')
    max_price = params.get('max_price', '')
    sort = params.get('sort', 'default')

    if selected_categories:
        products = products.filter(category_id__in=selected_categories)
    if min_price:
        try:
            products = products.filter(price__gte=float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            products = products.filter(price__lte=float(max_price))
        except ValueError:
            pass
    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page', 1)
    products_page = paginator.get_page(page_number)

    def build_url(**kwargs):
        new_params = params.copy()
        for key, value in kwargs.items():
            if value is not None and value != '':
                new_params[key] = value
            else:
                new_params.pop(key, None)
        return f"?{new_params.urlencode()}" if new_params else ""

    return render(request, 'main/catalog.html', {
        'game': game,
        'categories': categories,
        'products': products_page,
        'selected_categories': [int(c) for c in selected_categories],
        'min_price': min_price,
        'max_price': max_price,
        'current_sort': sort,
        'build_url': build_url,
    })


# wishlist_view
@login_required
def wishlist_view(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
    count = call_pg_function('get_wishlist_count', request.user.id)
    return render(request, 'main/wishlist.html', {
        'wishlist_items': wishlist_items,
        'wishlist_count': count,
    })


# toggle_wishlist
@login_required
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist_item, created = Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )
    if not created:
        wishlist_item.delete()
        action = 'removed'
    else:
        action = 'added'

    new_count = call_pg_function('get_wishlist_count', request.user.id)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'action': action,
            'count': new_count
        })
    return redirect('wishlist')


# catalog_all
def catalog_all(request):
    games = Game.objects.all()
    products = Product.objects.all()
    return render(request, 'main/catalog.html', {
        'games': games,
        'products': products,
        'selected_game': None
    })


# profile_edit_view
@login_required
def profile_edit_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user, user=request.user)
    return render(request, 'main/profile_edit.html', {'form': form})