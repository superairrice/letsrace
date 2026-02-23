import os

from .settings import *  # noqa
from django.core.exceptions import ImproperlyConfigured

DEBUG = False

# Production host/domain list from env (comma separated).
# Example: "thethe9.com,www.thethe9.com,127.0.0.1"
_prod_hosts = os.getenv("DJANGO_ALLOWED_HOSTS", "").strip()
if _prod_hosts:
    ALLOWED_HOSTS = [h.strip() for h in _prod_hosts.split(",") if h.strip()]

# Strict CORS default in production
CORS_ALLOW_ALL_ORIGINS = os.getenv("CORS_ALLOW_ALL_ORIGINS", "false").lower() == "true"

# Security headers/cookies (toggleable via env)
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "true").lower() == "true"
CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "true").lower() == "true"
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "false").lower() == "true"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
X_FRAME_OPTIONS = "SAMEORIGIN"

# HSTS is disabled by default to avoid accidental lock-in during initial setup.
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv("SECURE_HSTS_INCLUDE_SUBDOMAINS", "false").lower() == "true"
SECURE_HSTS_PRELOAD = os.getenv("SECURE_HSTS_PRELOAD", "false").lower() == "true"

# Production should use real SMTP backend
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")

required_db_env = ["DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT"]
missing_db_env = [k for k in required_db_env if not os.getenv(k)]
if missing_db_env:
    raise ImproperlyConfigured(
        "Missing required DB env vars for production: " + ", ".join(missing_db_env)
    )
