# gadget_cave/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.urls import reverse # Import reverse here as it's used in get_absolute_url


class CustomUser(AbstractUser):
    # Changed from 'phone' to 'phone_number' as per your latest code
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    # If you want an address field for CustomUser, add it here:
    # address = models.TextField(blank=True, null=True)

    # Add related_name to avoid clashes with auth.User
    groups = models.ManyToManyField(
        Group,
        verbose_name=('groups'),
        blank=True,
        help_text=(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="custom_user_groups",
        related_query_name="custom_user_group",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=('user permissions'),
        blank=True,
        help_text=('Specific permissions for this user.'),
        related_name="custom_user_permissions",
        related_query_name="custom_user_permission",
    )

    def __str__(self):
        return self.username


class Category(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('gadget_cave:product_list_by_category', args=[self.slug])


class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=200, db_index=True)
    # Direct main_image field on Product model as per your current code
    main_image = models.ImageField(upload_to='products/%Y/%m/%d', blank=True, null=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    available = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('name',)
        # Use 'indexes' instead of 'index_together' for Django 4.0+
        indexes = [
            models.Index(fields=['id', 'slug']),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('gadget_cave:product_detail', args=[self.id, self.slug])


# ProductImage for *additional* images, as main_image is directly on Product
class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE) # Used 'images' as related_name
    image = models.ImageField(upload_to='products/%Y/%m/%d/extra') # Renamed upload_to to differentiate
    description = models.CharField(max_length=255, blank=True, null=True) # Added null=True
    is_main = models.BooleanField(default=False) # This field might be redundant if main_image is on Product, consider removing if only for extra images

    def __str__(self):
        return f"Image for {self.product.name}"


class Cart(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user.username}"

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in {self.cart.user.username}'s cart"

    def get_cost(self):
        return self.product.price * self.quantity


class Order(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='orders', null=True, blank=True,) # Changed to null=True, blank=True for guest orders
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    paid = models.BooleanField(default=False)
    # product_name = models.ForeignKey(Product, on_delete=models.CASCADE,default=None)
    
    # Changed from upi_transaction_id to transaction_id to match admin.py's list_display
    transaction_id = models.CharField(max_length=100, blank=True, null=True) 

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=15, blank=True, null=True)

    # --- ADDED NEW FIELDS AS PER YOUR LATEST CODE AND ADMIN.PY REQUIREMENTS ---
    house_shop_no = models.CharField(max_length=100, blank=True, null=True)
    address = models.CharField(max_length=250) # Assuming this is the full address, not just street
    landmark = models.CharField(max_length=250, blank=True, null=True)
    city = models.CharField(max_length=100)
    district = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20)

    # --- ADDED STATUS AND PAYMENT STATUS FIELDS AS PER ADMIN.PY REQUIREMENTS ---
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return f'Order {self.id}'

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())
    def get_product_names(self):
        return ", ".join([item.product.name for item in self.items.all()])
    get_product_names.short_description = "Products"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2) # Price at the time of order
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return str(self.id)

    def get_cost(self):
        return self.price * self.quantity