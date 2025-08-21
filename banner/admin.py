from django.contrib import admin
from . models import Banner
from django.utils.html import format_html


class BannerAdmin(admin.ModelAdmin):
    list_display = ('banner_title', 'slug', 'created_date', 'updated_date', 'status','image_preview')
    prepopulated_fields = {'slug': ('banner_title',)}
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.banner_image:
            return format_html('<img src="{}" width="80" height="80" style="object-fit:cover;" />', obj.banner_image.url)
        return "No image"
    
    image_preview.short_description = 'Image'
    

# Register your models here.
admin.site.register(Banner, BannerAdmin)
