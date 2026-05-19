import os

from django.core.management import call_command
from django.db import OperationalError, ProgrammingError


def bootstrap_vercel_sqlite():
    if not os.environ.get('VERCEL'):
        return
    if os.environ.get('USE_SQLITE', 'False') != 'True':
        return

    try:
        call_command('migrate', interactive=False, verbosity=0)
        ensure_default_admin()
    except (OperationalError, ProgrammingError):
        # Let the request surface the real database error if bootstrap cannot run.
        return


def ensure_default_admin():
    username = os.environ.get('DEFAULT_ADMIN_USERNAME')
    password = os.environ.get('DEFAULT_ADMIN_PASSWORD')
    email = os.environ.get('DEFAULT_ADMIN_EMAIL', '')

    if not username or not password:
        return

    from django.contrib.auth import get_user_model

    User = get_user_model()
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': email,
            'is_staff': True,
            'is_superuser': True,
            'role': 'ADMIN',
        },
    )
    if created or os.environ.get('SYNC_DEFAULT_ADMIN_PASSWORD', 'True') == 'True':
        user.set_password(password)
        if not user.is_active:
            user.is_active = True
        if not user.is_staff:
            user.is_staff = True
        if not user.is_superuser:
            user.is_superuser = True
        user.save(update_fields=['password', 'is_active', 'is_staff', 'is_superuser'])
