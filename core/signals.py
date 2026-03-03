from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Resource, Bookmark

@receiver(post_save, sender=Resource)
def update_upload_count_on_save(sender, instance, created, **kwargs):
    """Update user upload count when a resource is saved"""
    if created and instance.uploader:
        user = instance.uploader
        user.upload_count = Resource.objects.filter(uploader=user).count()
        user.save()

@receiver(post_delete, sender=Resource)
def update_upload_count_on_delete(sender, instance, **kwargs):
    """Update user upload count when a resource is deleted"""
    if instance.uploader:
        user = instance.uploader
        user.upload_count = Resource.objects.filter(uploader=user).count()
        user.save()