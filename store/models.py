from django.db import models
from category.models import Category
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils import timezone

# Create your models here.
class Product(models.Model):
    owner = models.ForeignKey(  # who submitted it
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="products",
        null=True, 
        blank=True,  # allow null for old data / admin-created
    )
    product_name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(max_length=1000, blank=True)
    price = models.IntegerField()
    discount_price = models.FloatField(blank=True, null=True)
    images = models.ImageField(upload_to='photos/products/')
    stock = models.IntegerField()
    status = models.BooleanField(default=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    
    # single approval switch
    is_approved = models.BooleanField(default=False)
    
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.discount_price and self.discount_price >= self.price:
            raise ValidationError("Discount price must be less than the original price.")
    
    def get_url(self):
        # self.category.slug is slug of category, and self.slug is slug of product
        return reverse('product_detail', args=[self.category.slug, self.slug])

    
    def __str__(self):
        return self.product_name
    
variation_category_choices = {
    ('color', 'Color'),
    ('size', 'Size'),
}

# To modify the query set
class VariationManager(models.Manager):
    def colors(self):
        return super(VariationManager, self).filter(variation_category = 'color', is_active=True)
    
    def sizes(self):
        return super(VariationManager, self).filter(variation_category='size', is_active=True)
    
    
class Variation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variation_category = models.CharField(max_length=100, choices=variation_category_choices)
    variation_value = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now=True)
    
    # Telling the model about the variation manager
    objects = VariationManager()
    
    def __str__(self):
        return self.variation_value

class Review(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    review_text = models.TextField(max_length=1000)
    review_image = models.ImageField(upload_to='photos/reviews/', blank=True, null=True)
    rating = models.IntegerField(choices=[(1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')])
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"Review by {self.user.username} on {self.product.product_name}"
    
    
