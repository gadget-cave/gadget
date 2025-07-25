from django.urls import path
from . import views

app_name = 'gadget_cave'

urlpatterns = [
    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Home and Products
    path('', views.home, name='home'),
    path('category/<slug:category_slug>/', views.product_list_by_category, name='product_list_by_category'),
    path('product/<int:id>/<slug:slug>/', views.product_detail, name='product_detail'),

    # Cart
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('cart/', views.cart_detail, name='cart_detail'),

   # Buy Now URL
    path('buy_now/<int:product_id>/', views.buy_now, name='buy_now'),

    # Orders
    path('order/create/', views.order_create, name='order_create'),
    path('order/payment/<int:order_id>/', views.order_payment, name='order_payment'),
    path('order/confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('order/payment/<int:order_id>/confirm/', views.confirm_payment, name='confirm_payment'),
    path('order/confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
]



#     path('order/create/', views.order_create, name='order_create'),
#     path('order/payment/<int:order_id>/', views.order_payment, name='order_payment'),
#     path('order/confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
#     path('my-orders/', views.my_orders, name='my_orders'),
# 