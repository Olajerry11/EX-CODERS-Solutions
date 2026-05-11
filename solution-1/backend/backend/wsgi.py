"""
backend/backend/wsgi.py

WSGI config for the backend project.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
application = get_wsgi_application()
