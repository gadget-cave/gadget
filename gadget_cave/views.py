from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Category, Cart, CartItem, Order, OrderItem, CustomUser # Ensure CustomUser is imported
from .forms import CartAddProductForm, OrderCreateForm, CustomUserCreationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction # For atomic operations
from django.contrib.auth.forms import AuthenticationForm # Imported here for login_view
from django.shortcuts import render, get_object_or_404, redirect

def home(request):
    products = Product.objects.filter(available=True)
    categories = Category.objects.all()
    return render(request, 'gadget_cave/product/list.html', {'products': products, 'categories': categories})

def product_list_by_category(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    return render(request, 'gadget_cave/product/list.html', {
        'category': category,
        'categories': categories,
        'products': products
    })

def product_detail(request, id, slug):
    product = get_object_or_404(Product, id=id, slug=slug, available=True)
    cart_product_form = CartAddProductForm()
    return render(request, 'gadget_cave/product/detail.html', {
        'product': product,
        'cart_product_form': cart_product_form
    })



@login_required
def cart_detail(request):
    cart = None
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        # If the cart doesn't exist, it means the user hasn't added anything yet.
        # We can just pass a None cart or an empty list of items.
        pass # cart remains None

    except Exception as e:
        # This handles the "ValueError: Cannot query 'hisham'" or similar
        # if the user object itself is problematic before the database reset.
        messages.error(request, f"There was an error loading your cart: {e}. Please try logging in again or contact support.")
        cart = None # Ensure cart is None to prevent further errors
        # It's good practice to log this error too in a real application

    # This line is correct for the template path 'gadget_cave/cart/details.html'
    return render(request, 'gadget_cave/cart/details.html', {'cart': cart})
@login_required
def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    # Get or create cart for the logged-in user
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    form = CartAddProductForm(request.POST)
    if form.is_valid():
        quantity = form.cleaned_data['quantity']
        
        # Check if requested quantity exceeds available stock
        if quantity > product.stock:
            messages.error(request, f'Only {product.stock} items of {product.name} are available.')
            return redirect('gadget_cave:product_detail', id=product.id, slug=product.slug)

        # Try to get the item, if it exists, update quantity
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, product=product,
            defaults={'quantity': quantity}
        )
        if not created:
            # If item already in cart, update quantity
            if cart_item.quantity + quantity > product.stock:
                messages.error(request, f'Adding {quantity} more {product.name}(s) would exceed stock. Current in cart: {cart_item.quantity}, Stock: {product.stock}.')
                return redirect('gadget_cave:product_detail', id=product.id, slug=product.slug)
            cart_item.quantity += quantity
            cart_item.save()
        messages.success(request, f'{quantity} x {product.name} added to your cart.')
    return redirect('gadget_cave:cart_detail')

@login_required
def cart_remove(request, product_id):
    cart = get_object_or_404(Cart, user=request.user)
    product = get_object_or_404(Product, id=product_id)
    cart_item = get_object_or_404(CartItem, cart=cart, product=product)
    cart_item.delete()
    messages.success(request, f'{product.name} removed from your cart.')
    return redirect('gadget_cave:cart_detail')
# gadget_cave/views.py


@login_required
def buy_now(request, product_id):
    product = get_object_or_404(Product, id=product_id, available=True)

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))

        if quantity <= 0:
            messages.error(request, 'Quantity must be at least 1.')
            return redirect('gadget_cave:product_detail', id=product.id, slug=product.slug)

        if quantity > product.stock:
            messages.error(request, f'Only {product.stock} items of {product.name} are available.')
            return redirect('gadget_cave:product_detail', id=product.id, slug=product.slug)

        # Store product details in session for the order_create view
        request.session['buy_now_product_id'] = product_id
        request.session['buy_now_quantity'] = quantity
        messages.info(request, f'Please provide your shipping details for {product.name}.')
        return redirect('gadget_cave:order_create') # <--- THIS IS THE CRITICAL CHANGE

    else:
        messages.info(request, "Please confirm your intention to buy now.")
        return redirect('gadget_cave:product_detail', id=product.id, slug=product.slug)

# gadget_cave/views.py

@login_required
def order_create(request):
    # Buy Now ഫ്ലോയിൽ നിന്ന് പ്രോഡക്റ്റ് വിവരങ്ങൾ ലഭിക്കുകയാണെങ്കിൽ
    buy_now_product_id = request.session.get('buy_now_product_id')
    buy_now_quantity = request.session.get('buy_now_quantity', 1)

    products_to_order_display = [] # ടെംപ്ലേറ്റിൽ കാണിക്കാൻ
    total_order_cost = 0
    is_buy_now_flow = False # ടെംപ്ലേറ്റിൽ Buy Now ഫ്ലോ ആണോ എന്ന് അറിയാൻ

    if buy_now_product_id:
        # ഇത് Buy Now ഫ്ലോ ആണ്
        is_buy_now_flow = True
        product = get_object_or_404(Product, id=buy_now_product_id, available=True)
        # സ്റ്റോക്ക് വീണ്ടും ഇവിടെയും പരിശോധിക്കുക
        if buy_now_quantity > product.stock:
            messages.error(request, f'Only {product.stock} items of {product.name} are available for Buy Now.')
            del request.session['buy_now_product_id']
            if 'buy_now_quantity' in request.session: del request.session['buy_now_quantity']
            return redirect('gadget_cave:product_detail', id=product.id, slug=product.slug)

        products_to_order_display.append({'product': product, 'quantity': buy_now_quantity, 'price': product.price})
        total_order_cost = product.price * buy_now_quantity

    else:
        # ഇത് കാർട്ട് ഫ്ലോ ആണ്
        cart = get_object_or_404(Cart, user=request.user)
        if not cart.items.exists():
            messages.warning(request, 'Your cart is empty. Please add items before placing an order.')
            return redirect('gadget_cave:cart_detail')

        # കാർട്ടിലെ സ്റ്റോക്ക് പരിശോധിക്കുക
        for item in cart.items.all():
            if item.quantity > item.product.stock:
                messages.error(request, f'Not enough stock for {item.product.name}. Only {item.product.stock} available in stock, but you have {item.quantity} in cart.')
                return redirect('gadget_cave:cart_detail')
            products_to_order_display.append({'product': item.product, 'quantity': item.quantity, 'price': item.product.price})
        total_order_cost = cart.get_total_cost()

    # ഓർഡർ ചെയ്യാൻ പ്രോഡക്റ്റുകൾ ഇല്ലെങ്കിൽ
    if not products_to_order_display:
        messages.error(request, "No products to order. Please add items to cart or use Buy Now.")
        return redirect('gadget_cave:home')


    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                order = form.save(commit=False)
                order.user = request.user # ലോഗിൻ ചെയ്ത യൂസറിനെ ഓർഡറിലേക്ക് ചേർക്കുക
                order.save()

                # Buy Now ആണെങ്കിൽ ഒരു പ്രോഡക്റ്റും, കാർട്ട് ആണെങ്കിൽ കാർട്ടിലുള്ളതെല്ലാം ഓർഡർ ഐറ്റംസ് ആക്കുക
                for item_data in products_to_order_display:
                    product = item_data['product']
                    quantity = item_data['quantity']
                    price = item_data['price']

                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        price=price,
                        quantity=quantity
                    )
                    # സ്റ്റോക്ക് കുറയ്ക്കുക
                    product.stock -= quantity
                    product.save()

                # സെഷൻ വേരിയബിൾ ക്ലിയർ ചെയ്യുക (Buy Now ആണെങ്കിൽ)
                if buy_now_product_id:
                    del request.session['buy_now_product_id']
                    if 'buy_now_quantity' in request.session: del request.session['buy_now_quantity']

                # കാർട്ട് ക്ലിയർ ചെയ്യുക (കാർട്ട് ഫ്ലോ ആണെങ്കിൽ)
                else: # buy_now_product_id ഇല്ലെങ്കിൽ അത് കാർട്ട് ആണ്
                    cart.items.all().delete()

                messages.success(request, 'Your order details have been saved. Please proceed to payment.')
                return redirect('gadget_cave:order_payment', order_id=order.id)
        else:
            messages.error(request, 'Please correct the errors in the shipping information.')
    else:
        # GET request ആണെങ്കിൽ, ഫോം pre-fill ചെയ്യുക
        initial_data = {
            'first_name': getattr(request.user, 'first_name', ''),
            'last_name': getattr(request.user, 'last_name', ''),
            'email': getattr(request.user, 'email', ''),
            'phone': getattr(request.user, 'phone_number', ''),
            'address': getattr(request.user, 'address', ''), # പഴയ address ഫീൽഡ്
            'postal_code': getattr(request.user, 'postal_code', ''),
            'city': getattr(request.user, 'city', ''),
            # പുതിയ ഫീൽഡുകൾ pre-fill ചെയ്യണമെങ്കിൽ CustomUser മോഡലിൽ അവ ചേർത്തിരിക്കണം
            'house_shop_no': getattr(request.user, 'house_shop_no', ''),
            'landmark': getattr(request.user, 'landmark', ''),
            'district': getattr(request.user, 'district', ''),
            'state': getattr(request.user, 'state', ''),
        }
        form = OrderCreateForm(initial=initial_data)

    context = {
        'form': form,
        'products_to_order': products_to_order_display,
        'total_order_cost': total_order_cost,
        'buy_now_flow': is_buy_now_flow
    }
    return render(request, 'gadget_cave/order/create.html', context)
@login_required
def order_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.paid:
        messages.info(request, "This order has already been paid.")
        return redirect('gadget_cave:order_confirmation', order_id=order.id)

    total_amount = order.get_total_cost()
    upi_id = "hixzam313@okaxis" # Replace with your actual UPI ID
    upi_url = f"upi://pay?pa={upi_id}&pn=GadgetCavePayment&am={total_amount}&cu=INR&tr={order.id}"
    
    context = {
        'order': order,
        'total_amount': total_amount,
        'upi_url': upi_url,
        'upi_id': upi_id, # Pass UPI ID for display
    }
    return render(request, 'gadget_cave/order/payment.html', context)

@login_required
def confirm_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if request.method == 'POST':
        # Get UPI transaction ID from the form if provided
        upi_transaction_id = request.POST.get('upi_transaction_id', '')

        with transaction.atomic():
            order.paid = True  # Mark order as paid
            if upi_transaction_id:
                order.upi_transaction_id = upi_transaction_id # Save the transaction ID
            order.save()
            messages.success(request, 'Your payment has been confirmed! Order placed successfully.')
            return redirect('gadget_cave:order_confirmation', order_id=order.id)
    messages.error(request, 'Invalid request for payment confirmation.')
    return redirect('gadget_cave:order_payment', order_id=order.id) # Redirect back to payment if invalid

@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'gadget_cave/order/confirmation.html', {'order': order})

@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created')
    return render(request, 'gadget_cave/account/my_orders.html', {'orders': orders})

# Authentication views
def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) # Log the user in after successful registration
            messages.success(request, 'Registration successful. Welcome!')
            return redirect('gadget_cave:home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'gadget_cave/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('gadget_cave:home')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                # Redirect to a 'next' URL if provided, otherwise home
                next_url = request.GET.get('next') or 'gadget_cave:home'
                return redirect(next_url)
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'gadget_cave/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('gadget_cave:home')