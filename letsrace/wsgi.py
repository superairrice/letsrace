"""
WSGI config for letsrace project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/wsgi/
"""

# import os

# from django.core.wsgi import get_wsgi_application

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'letsrace.settings')

# application = get_wsgi_application()


from django.core.wsgi import get_wsgi_application
import os
import sys

path = os.path.abspath(__file__+'/,,/')

if path not in sys.path:
    sys.path.insert(0, path)


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'letsrace.settings_prod')

application = get_wsgi_application()
