from django.contrib import admin
from . models import Product, Variation, Review
from django.utils.html import format_html

# Register your models here.

class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'price', 'stock', 'category','is_approved', 'updated_date', 'status', 'image_preview')
    prepopulated_fields = {'slug': ('product_name',)}
    list_filter = ("is_approved", "status", "category")
    search_fields = ("product_name", "owner__email", "owner__first_name")
    list_editable = ("is_approved", "status")  # approve directly in list page
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.images:
            return format_html('<img src="{}" width="80" height="80" style="object-fit:cover;" />', obj.images.url)
        return "No image"
    
    image_preview.short_description = 'Image'
    
class VariationAdmin(admin.ModelAdmin):
    list_display = ('product','variation_category','variation_value', 'is_active')
    list_editable = ('is_active',) # approve directly from the list
    list_filter = ('product','variation_category','variation_value')

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'rating', 'created_at', 'review_image_preview')
    list_filter = ('product', 'rating', 'user', 'created_at')
    search_fields = ('user__username', 'product__product_name')
    readonly_fields = ('review_image_preview',)
    list_editable = ('rating',)  # Allows to directly update ratings from the admin panel

    def review_image_preview(self, obj):
        if obj.review_image:
            return format_html('<img src="{}" width="80" height="80" style="object-fit:cover;" />', obj.review_image.url)
        return "No image"
    
    review_image_preview.short_description = 'Review Image'

admin.site.register(Product, ProductAdmin)
admin.site.register(Variation, VariationAdmin)
admin.site.register(Review, ReviewAdmin)



