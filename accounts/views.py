from django.shortcuts import render
from .forms import RegistrationForm
from . models import Account
from django.shortcuts import redirect, get_object_or_404, HttpResponse
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from .forms import ProfileUpdateForm
from store.forms import ProductForm
from django.utils.text import slugify
from store.models import Product
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F
from carts.models import Cart, CartItem
# Password change
from . forms import CustomPasswordChangeForm
from django.contrib.auth import update_session_auth_hash

# Email verification
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage

from carts.views import _cart_id

def user_login(request):
    if request.method == "POST":
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        
        # Returns user object
        user = auth.authenticate(email=email, password=password)
        
        if user is not None:
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                is_cart_item_exists = CartItem.objects.filter(cart=cart).exists()
                if is_cart_item_exists:
                    cart_item = CartItem.objects.filter(cart=cart)
                    
                    # Getting product variation by cart id
                    product_variation = []
                    for item in cart_item:
                        variation = item.variations.all()
                        product_variation.append(list(variation))
                    
                    # Get the cart items from the user to access his product variations
                    cart_item = CartItem.objects.filter(user=user)
            
                    # existing variations, current variation, item id needed
                    # If the current variation is inside the existing variations, then increase
                    
                    ex_var_list = []
                    id = []
                    for item in cart_item:
                        existing_variation = item.variations.all()
                        ex_var_list.append(list(existing_variation))
                        id.append(item.id)
                    
                    # product_variation = [1, 2, 3, 4, 6]
                    # ex_var_list = [4, 5, 3, 5]
                    for pr in product_variation:
                        if pr in ex_var_list:
                            index = ex_var_list.index(pr)
                            item_id = id[index]
                            item = CartItem.objects.get(id=item_id)
                            item.quantity += 1
                            item.user = user
                            item.save()
                        else:
                            cart_item = CartItem.objects.filter(cart=cart)
                            for item in cart_item:
                                item.user = user
                                item.save()
            except:
                pass
            auth.login(request, user)
            messages.success(request, "You are now logged in.")
            # Redirect to next page if provided
            next_url = request.GET.get('next') or request.POST.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('user_dashboard')
        
        else:
            messages.error(request, "Invalid login credentials.")
            return redirect('user_login')
    # return render(request, 'accounts/login.html')
    return render(request, 'accounts/login.html', {'next': request.GET.get('next')})


def user_register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            phone_number = form.cleaned_data['phone_number']
            password = form.cleaned_data['password']
            username = email.split("@")[0]

            # We cannot add phone number here, as in the create_user method this is not there
            user = Account.objects.create_user(
                first_name=first_name, 
                last_name=last_name, 
                username=username,
                email=email,
                password=password,
                )
            # Updates the user object
            user.phone_number = phone_number
            user.save()
            
            # User Activation
            current_site = get_current_site(request)
            mail_subject = 'Please Activate your account'
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            message = render_to_string('accounts/verification/account_verification.html', {
                'user': user,
                'domain': current_site,
                # Encoding user id with url safe base 64 encode so noone can see the pk
                'uid': uid,
                # Creates token for this user, later we check token upon verification
                'token': token
            })
            to_email = email
            try:
                send_email = EmailMessage(
                    mail_subject, message, to=[to_email]
                )
                send_email.send()
                # messages.success(request, "Account created. Check your email to activate your account.")
            except Exception:
                messages.warning(request, "Account created, but we couldn't send the email. Ask admin to activate you.")
            
            return redirect("/accounts/login/?command=verification&email="+email)
            
    else:
        form = RegistrationForm()
    
    context = {
        'form': form
    }
    return render(request, 'accounts/register.html', context)


@login_required(login_url = 'user_login')
def user_logout(request):
    auth.logout(request)
    messages.success(request, "You are logged out.")
    return redirect('home')

def account_activate(request, uidb64, token):
    try:
        # Decodes the uidb and stores in uid, gives pk of user
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None
    
    # Checks the token
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Congratulations! Your  account is activated.")
        return redirect('user_login')
    else:
        messages.error(request, "Invalid Activation Link")
        return redirect('user_register')


@login_required(login_url = 'user_login')
def user_dashboard(request):
    user = request.user
    # Products posted by this user
    my_products_qs = Product.objects.filter(owner=user)
    
    context = {
        # Product stats (seller side)
        "my_products_total": my_products_qs.count(),
        "my_products_approved": my_products_qs.filter(is_approved=True).count(),
        "my_products_pending": my_products_qs.filter(is_approved=False).count(),
        "my_products_active": my_products_qs.filter(status=True).count(),
        "my_products_inactive": my_products_qs.filter(status=False).count(),
        
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required(login_url='user_login')
def my_products(request):
    qs = (
        Product.objects.filter(
        owner=request.user
        ).select_related('category')
        .order_by('-created_date')
    )
    
    # Quick stats
    stats = {
        "total": qs.count(),
        "approved": qs.filter(is_approved=True).count(),
        "pending": qs.filter(is_approved=False).count(),
        "inactive": qs.filter(status=False).count(),
    }
    
    paginator = Paginator(qs, 10)
    page = request.GET.get('page')
    products = paginator.get_page(page)

    return render(request, "accounts/my_products.html", {
        "products": products,
        "stats": stats,
    })

@login_required(login_url='user_login')
def delete_product(request, product_id):
    p = get_object_or_404(Product, id=product_id, owner=request.user)
    p.delete()
    messages.success(request, "Product deleted.")
    return redirect('my_products')


@login_required(login_url='user_login')
def edit_product(request, product_id):
    # p = get_object_or_404(Product, id=product_id, owner=request.user)
    product = get_object_or_404(Product, id=product_id, owner=request.user)
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product updated.")
            return redirect("my_products")
    else:
        form = ProductForm(instance=product)
    return render(request, "accounts/add_product.html", {"form": form})


@login_required(login_url = 'user_login')
def my_orders(request):
    return render(request, 'accounts/my_orders.html')

@login_required(login_url = 'user_login')
def add_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            p = form.save(commit=False)
            p.owner = request.user
            p.is_approved = False     # pending by default
            
            # Auto slug (unique)
            base = slugify(p.product_name)
            slug = base or "product"
            i = 1
            while Product.objects.filter(slug=slug).exists():
                i += 1
                slug = f"{base}-{i}"
            p.slug = slug
            p.save()
            messages.success(request, "Submitted! Waiting for admin approval.")
            return redirect("my_products")
    else:
        form = ProductForm()
    return render(request, "accounts/add_product.html", {"form": form})


@login_required(login_url = 'user_login')
def edit_profile(request):
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('edit_profile')
    else:
        form = ProfileUpdateForm(instance=request.user)

    return render(request, 'accounts/edit_profile.html', {"form": form})

@login_required(login_url = 'user_login')
def change_password(request):
    if request.method == "POST":
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Keep the user logged in after password change
            update_session_auth_hash(request, user)
            messages.success(request, "Your password was updated successfully.")
            return redirect("user_dashboard")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomPasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {'form': form})
