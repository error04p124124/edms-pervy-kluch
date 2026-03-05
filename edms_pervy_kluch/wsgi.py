"""
WSGI config for edms_pervy_kluch project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edms_pervy_kluch.settings')

application = get_wsgi_application()
