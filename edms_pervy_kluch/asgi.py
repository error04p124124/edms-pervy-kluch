"""
ASGI config for edms_pervy_kluch project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edms_pervy_kluch.settings')

application = get_asgi_application()
