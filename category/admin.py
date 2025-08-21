from django.contrib import admin
from . models import Category
from django.utils.html import format_html


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('category_name', 'slug', 'created_date', 'updated_date','status', 'image_preview')
    prepopulated_fields = {'slug': ('category_name',)}
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.category_image:
            return format_html('<img src="{}" width="80" height="80" style="object-fit:cover;" />', obj.category_image.url)
        return "No image"
    
    image_preview.short_description = 'Image'
    

# Register your models here.
admin.site.register(Category, CategoryAdmin)
