# gadget_cave/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import Category, Product, ProductImage, Order, OrderItem, Cart, CartItem, CustomUser
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# Custom User Admin
@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    # 'phone' എന്നുള്ളത് 'phone_number' എന്ന് തിരുത്തണം, കാരണം നിങ്ങളുടെ CustomUser മോഡലിൽ phone_number ആണ്
    # 'address' എന്ന ഫീൽഡ് CustomUser മോഡലിൽ ഇല്ലാത്തതുകൊണ്ട് ഒഴിവാക്കുന്നു.
    list_display = BaseUserAdmin.list_display + ('phone_number',)
    fieldsets = BaseUserAdmin.fieldsets + (
        (('Custom Fields'), {'fields': ('phone_number',)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (('Custom Fields'), {'fields': ('phone_number',)}),
    )

# Category Admin
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']

# ProductImage Inline
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'is_main', 'description', 'image_preview']
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="auto" style="border-radius: 5px;" />', obj.image.url)
        return "(No Image)"
    image_preview.short_description = "Image Preview"

# Product Admin
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'price', 'stock', 'available', 'created', 'updated', 'category', 'main_image_preview']
    list_filter = ['available', 'created', 'updated', 'category']
    list_editable = ['price', 'stock', 'available']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]
    search_fields = ['name', 'description']
    raw_id_fields = ['category']

    def main_image_preview(self, obj):
        if obj.main_image:
            return format_html('<img src="{}" width="50" height="auto" style="border-radius: 3px;" />', obj.main_image.url)
        return "(No Main Image)"
    main_image_preview.short_description = "Main Image"

# OrderItem Inline (This is what enables showing product details inside an order)
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_display_name', 'product_category', 'price', 'quantity', 'get_cost_display']
    fields = ['product', 'product_display_name', 'product_category', 'price', 'quantity', 'get_cost_display']
    raw_id_fields = ['product']

    def product_display_name(self, obj):
        return obj.product.name if obj.product else "N/A"
    product_display_name.short_description = 'Product Name'

    def product_category(self, obj):
        return obj.product.category if obj.product else "N/A"
    product_category.short_description = 'Category'

    def get_cost_display(self, obj):
        return f"₹{obj.get_cost():.2f}"
    get_cost_display.short_description = 'Item Total'

# Order Admin
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # list_display = [
    #     'id', 'user_display_name', 'first_name', 'last_name', 'email',
    #     'phone', 'house_shop_no', 'address', 'landmark', 'city', 'district', 'state', 'postal_code',
    #     'paid', 'transaction_id',
    #     'created', 'updated', 'status', 'payment_status', 'get_total_cost_display'
    # ]
    list_display = [
    'id', 'user_display_name', 'first_name', 'last_name', 'email',
    'phone', 'house_shop_no', 'address', 'landmark', 'city', 'district', 'state', 'postal_code',
    'paid', 'transaction_id',
    'get_product_names',  # ✅ Add this line here
    'created', 'updated', 'status', 'payment_status', 'get_total_cost_display'
]
    list_filter = ['paid', 'created', 'updated', 'status', 'payment_status']
    search_fields = ['user__username', 'first_name', 'last_name', 'email', 'transaction_id', 'phone']
    inlines = [OrderItemInline] # This line is crucial for displaying order items

    def user_display_name(self, obj):
        return obj.user.username if obj.user else "Guest"
    user_display_name.short_description = 'User'

    def get_total_cost_display(self, obj):
        return f"₹{obj.get_total_cost():.2f}"
    get_total_cost_display.short_description = 'Order Total'

    actions = ['make_paid', 'mark_as_shipped']

    def make_paid(self, request, queryset):
        updated = queryset.update(paid=True, payment_status='completed')
        self.message_user(request, f'{updated} orders were successfully marked as paid.')
    make_paid.short_description = 'Mark selected orders as paid'

    def mark_as_shipped(self, request, queryset):
        updated = queryset.update(status='shipped')
        self.message_user(request, f'{updated} orders were successfully marked as shipped.')
    mark_as_shipped.short_description = 'Mark selected orders as shipped'

# Cart Admin
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user_display_name', 'created_at', 'updated_at', 'get_total_cost_display']
    search_fields = ['user__username']
    inlines = []

    def user_display_name(self, obj):
        return obj.user.username if obj.user else "N/A"
    user_display_name.short_description = 'User'

    def get_total_cost_display(self, obj):
        return f"₹{obj.get_total_cost():.2f}" if hasattr(obj, 'get_total_cost') else "N/A"
    get_total_cost_display.short_description = 'Cart Total'

# CartItem Admin
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart_user', 'product_name', 'quantity', 'get_item_cost_display']
    list_filter = ['cart']
    search_fields = ['cart__user__username', 'product__name']

    def cart_user(self, obj):
        return obj.cart.user.username if obj.cart and obj.cart.user else "N/A"
    cart_user.short_description = 'Cart User'

    def product_name(self, obj):
        return obj.product.name if obj.product else "N/A"
    product_name.short_description = 'Product'

    def get_item_cost_display(self, obj):
        return f"₹{obj.get_cost():.2f}" if hasattr(obj, 'get_cost') else "N/A"
    get_item_cost_display.short_description = 'Item Total'