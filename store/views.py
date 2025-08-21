from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404
from .models import Product, Review
from category.models import Category
from carts.models import CartItem
from carts.views import _cart_id
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import ContactSellerForm, ReviewForm

def store(request, category_slug=None):
    categories = None
    products = None
    
    if category_slug:
        categories = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(category=categories, status=True, is_approved=True)
    else:
        products = Product.objects.filter(status=True, is_approved=True).order_by('id')
        
    paginator = Paginator(products, 3)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)
    product_count = products.count()
    
    context = {
        'products': paged_products,
        'product_count': product_count,
    }
    
    return render(request, 'store/store.html', context)

@login_required(login_url='user_login')
def product_detail(request, category_slug, product_slug):
    try:
        product = Product.objects.get(category__slug=category_slug, slug=product_slug)
        if not product.is_approved and not (request.user.is_staff or request.user == product.owner):
            raise Http404("Product not found")

        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=product).exists()
    
    except Product.DoesNotExist:
        raise Http404("Product not found")

    has_reviewed = Review.objects.filter(user=request.user, product=product).exists() if request.user.is_authenticated else False
    reviews = product.reviews.all()
    edit_review_id = request.GET.get('edit_review_id')
    form = None

    # Handle POST for add/update/delete review
    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.error(request, "You must be logged in to leave a review.")
            return redirect('user_login')

        # Check if deleting review
        if 'delete_review' in request.POST:
            review_id_to_delete = request.POST.get('delete_review')
            review_to_delete = get_object_or_404(Review, id=review_id_to_delete, user=request.user)
            review_to_delete.delete()
            messages.success(request, "Your review has been deleted.")
            return redirect('product_detail', category_slug=category_slug, product_slug=product_slug)

        # Check if editing review
        if 'edit_review' in request.POST:
            review_id_to_edit = request.POST.get('edit_review')
            review_instance = get_object_or_404(Review, id=review_id_to_edit, user=request.user)
            form = ReviewForm(request.POST, request.FILES, instance=review_instance)
            if form.is_valid():
                form.save()
                messages.success(request, "Your review has been updated.")
                return redirect('product_detail', category_slug=category_slug, product_slug=product_slug)
            else:
                edit_review_id = review_id_to_edit  # keep form open if errors

        # Else adding a new review
        else:
            if has_reviewed:
                messages.error(request, "You have already reviewed this product.")
                return redirect('product_detail', category_slug=category_slug, product_slug=product_slug)
            form = ReviewForm(request.POST, request.FILES)
            if form.is_valid():
                review = form.save(commit=False)
                review.user = request.user
                review.product = product
                review.save()
                messages.success(request, "Your review has been submitted!")
                return redirect('product_detail', category_slug=category_slug, product_slug=product_slug)
    else:
        if edit_review_id:
            review_instance = get_object_or_404(Review, id=edit_review_id, user=request.user)
            form = ReviewForm(instance=review_instance)
        else:
            form = ReviewForm()

    context = {
        'product': product,
        'in_cart': in_cart,
        'form': form,
        'has_reviewed': has_reviewed,
        'reviews': reviews,
        'edit_review_id': int(edit_review_id) if edit_review_id else None,
    }

    return render(request, 'store/product_detail.html', context)


def search(request):
    keyword = request.GET.get('keyword', '').strip()
    if not keyword:
        return redirect('home')
    
    products = Product.objects.filter(
        status=True,
        is_approved=True
    ).filter(
        Q(description__icontains=keyword) | 
        Q(product_name__icontains=keyword)
    ).order_by('-created_date')

    product_count = products.count()
            
    context = {
        'products': products,
        'product_count': product_count,
        'keyword': keyword,
    }
    return render(request, 'store/store.html', context)

User = get_user_model()

def seller_profile(request, user_id):
    seller = get_object_or_404(User, pk=user_id)
    qs = Product.objects.filter(owner=seller, status=True, is_approved=True).order_by('-id')
    product_count = qs.count()

    paginator = Paginator(qs, 4)
    page = request.GET.get('page')
    products = paginator.get_page(page)

    context = {
        "seller": seller,
        "products": products,
        "product_count": product_count,
        "keyword": "",
    }
    return render(request, "accounts/seller/seller_profile.html", context)

def _display_name(user):
    name = f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip()
    return name or getattr(user, 'email', 'User')

@login_required(login_url="user_login")
def message_seller(request, user_id):
    seller = get_object_or_404(User, pk=user_id)

    if request.user.pk == seller.pk:
        messages.error(request, "You can't message yourself.")
        return redirect("seller_profile", user_id=seller.pk)

    if request.method == "POST":
        form = ContactSellerForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data["subject"]
            body = form.cleaned_data["message"]
            buyer = request.user

            product = None
            product_id = request.GET.get("product")
            if product_id:
                try:
                    product = Product.objects.get(pk=product_id)
                except Product.DoesNotExist:
                    product = None

            from messages.models import Message  # Ensure this is correct
            msg = Message.objects.create(
                sender=buyer,
                receiver=seller,
                subject=subject,
                body=body,
                product=product,
            )

            email_subject = f"[Marketplace] {subject}"
            email_body = (
                f"From: {_display_name(buyer)}\n"
                f"Email: {buyer.email}\n\n"
                f"{body}"
            )
            send_mail(
                email_subject,
                email_body,
                getattr(settings, "DEFAULT_FROM_EMAIL", None),
                [seller.email],
                fail_silently=True,
            )

            messages.success(request, "Your message was sent to the seller.")
            return redirect("message:message_detail", pk=msg.pk)
    else:
        form = ContactSellerForm()

    return render(request, "messages/message_seller.html", {"seller": seller, "form": form})



