"""Gunicorn WSGI entrypoint. Import intentionally fails on missing configuration."""

from sage_signing.server import make_application

application = make_application()
