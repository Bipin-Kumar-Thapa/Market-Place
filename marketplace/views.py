from django.shortcuts import render
from store.models import Product
from banner.models import Banner
from category.models import Category


def home(request):
    products = Product.objects.all().filter(status=True, is_approved=True)
    banners = Banner.objects.all().filter(status = True)
    categories = Category.objects.all().filter(status=True)
    
    context = {
        'products': products,
        'banners': banners,
        'categories': categories
    }
    return render(request, 'home/home.html', context)


def order_complete(request):
    return render(request, 'cart/order_complete.html')


