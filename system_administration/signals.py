from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from .models import General_Log
from django.contrib.auth.models import User
import threading

# Thread-local storage for request information
_thread_local = threading.local()

# Models to exclude from logging
EXCLUDED_MODELS = ['General_Log', 'Log', 'ContentType']

def create_general_log(instance, action):
    # Check if model should be excluded from logging
    if instance.__class__.__name__ in EXCLUDED_MODELS:
        return

    # Get current user using thread local storage
    user = getattr(_thread_local, 'user', None)

    log_details = {
        'action': action,
        'model': instance.__class__.__name__,
        'object_id': instance.pk,
        'user': str(user) if user else "Anonymous",
    }

    # Get content type
    content_type = ContentType.objects.get_for_model(instance.__class__)
    
    # Calculate update number (for tracking task updates)
    update_number = General_Log.objects.filter(
        content_type=content_type, object_id=instance.pk
    ).count() + 1

    General_Log.objects.create(
        content_type=content_type,
        object_id=instance.pk,
        log_details=log_details,
        update_number=update_number
    )

def should_log_model(sender):
    """Determine if the model should be logged based on certain criteria"""
    return (
        sender.__name__ not in EXCLUDED_MODELS and
        not sender._meta.abstract and
        sender._meta.app_label != 'contenttypes'
    )

@receiver(post_save)
def log_create_or_update(sender, instance, created, **kwargs):
    if should_log_model(sender):
        create_general_log(instance, 'create' if created else 'update')

@receiver(post_delete)
def log_delete(sender, instance, **kwargs):
    if should_log_model(sender):
        create_general_log(instance, 'delete')

# Function to set current user in thread local storage
def set_current_user(user):
    _thread_local.user = user