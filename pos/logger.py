# pos/logger.py
from django.utils import timezone
from django.contrib.auth.models import User
from .models import UserActivityLog
import json
import traceback

def log_activity(user, action_type, model_name, object_id=None, description=None, request=None, data=None):
    """
    Centralized logging function for all system activities.
    """
    try:
        ip_address = None
        user_agent = None
        
        if request:
            ip_address = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Create the log entry
        log_entry = UserActivityLog.objects.create(
            user=user,
            action_type=action_type,
            model_name=model_name,
            object_id=str(object_id) if object_id else None,
            description=description or f'{action_type} on {model_name}',
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return log_entry
        
    except Exception as e:
        print(f"Logging error: {e}")
        return None


def log_create(user, instance, request=None, description=None):
    return log_activity(
        user=user,
        action_type='create',
        model_name=instance.__class__.__name__,
        object_id=instance.pk,
        description=description or f'Created {instance.__class__.__name__}: {str(instance)}',
        request=request
    )


def log_update(user, instance, request=None, description=None):
    return log_activity(
        user=user,
        action_type='update',
        model_name=instance.__class__.__name__,
        object_id=instance.pk,
        description=description or f'Updated {instance.__class__.__name__}: {str(instance)}',
        request=request
    )


def log_delete(user, instance, request=None, description=None):
    return log_activity(
        user=user,
        action_type='delete',
        model_name=instance.__class__.__name__,
        object_id=instance.pk,
        description=description or f'Deleted {instance.__class__.__name__}: {str(instance)}',
        request=request
    )


def log_login(user, request=None):
    return log_activity(
        user=user,
        action_type='login',
        model_name='User',
        object_id=str(user.pk),
        description=f'User {user.username} logged in',
        request=request
    )


def log_logout(user, request=None):
    return log_activity(
        user=user,
        action_type='logout',
        model_name='User',
        object_id=str(user.pk),
        description=f'User {user.username} logged out',
        request=request
    )


def log_export(user, model_name, request=None, description=None):
    return log_activity(
        user=user,
        action_type='export',
        model_name=model_name,
        description=description or f'Exported {model_name} data',
        request=request
    )


def log_import(user, model_name, request=None, description=None, count=0):
    return log_activity(
        user=user,
        action_type='import',
        model_name=model_name,
        description=description or f'Imported {count} {model_name} records',
        request=request,
        data={'count': count}
    )


def log_print(user, model_name, object_id=None, request=None, description=None):
    return log_activity(
        user=user,
        action_type='print',
        model_name=model_name,
        object_id=str(object_id) if object_id else None,
        description=description or f'Printed {model_name}',
        request=request
    )


def log_error(user, model_name, request=None, description=None, error=None):
    return log_activity(
        user=user,
        action_type='error',
        model_name=model_name,
        description=description or f'Error: {str(error)}' if error else 'Error occurred',
        request=request,
        data={'error': str(error)} if error else None
    )


def log_view(user, model_name, object_id=None, request=None, description=None):
    return log_activity(
        user=user,
        action_type='view',
        model_name=model_name,
        object_id=str(object_id) if object_id else None,
        description=description or f'Viewed {model_name}',
        request=request
    )