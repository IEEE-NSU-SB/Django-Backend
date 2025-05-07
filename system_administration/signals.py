from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from system_administration.system_logs import System_Logs

# Models to exclude from logging
EXCLUDED_MODELS = ['General_Log', 'ContentType', 'Task_Log','migration', 'auth', 'Session']

def create_general_log(instance, action):
    # Check if model should be excluded from logging
    # try:
        if instance.__class__.__name__ in EXCLUDED_MODELS:
            return
        
        System_Logs.save_logs(instance, action)
        
             
    # except Exception as e:
    #     pass

def should_log_model(sender):
    """Determine if the model should be logged based on certain criteria"""
    return (
        sender.__name__ not in EXCLUDED_MODELS and
        not sender._meta.abstract and
        sender._meta.app_label != 'contenttype'
    )

@receiver(post_save)
def log_create_or_update(sender, instance, created, **kwargs):
    if should_log_model(sender):
        create_general_log(instance, 'create' if created else 'update')

@receiver(post_delete)
def log_delete(sender, instance, **kwargs):
    if should_log_model(sender):
        create_general_log(instance, 'delete')