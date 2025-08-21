from django.db import models

# Create your models here.
class Banner(models.Model):
    banner_title = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    url = models.CharField(max_length=200, blank=True, null=True)
    banner_image = models.ImageField(upload_to="photos/banners", blank=True, null=True)
    banner_video = models.FileField(upload_to="videos/banners", blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    status = models.BooleanField(default=True)
    
    
    class Meta:
        verbose_name = 'banner'
        verbose_name_plural = 'banners'
        
    def __str__(self):
        return self.banner_title
