from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from .models import Banner
from utils.media_cleanup import delete_old_file_on_update, delete_file_on_delete

@receiver(pre_save, sender=Banner)
def banner_image_update_cleanup(sender, instance, **kwargs):
    delete_old_file_on_update(instance, Banner, 'banner_image')

@receiver(post_delete, sender=Banner)
def banner_image_delete_cleanup(sender, instance, **kwargs):
    delete_file_on_delete(instance, 'banner_image')
