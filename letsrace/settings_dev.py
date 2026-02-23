import os

from .settings import *  # noqa

# Local development defaults
DEBUG = True

# Keep local convenience hosts enabled
ALLOWED_HOSTS = list(dict.fromkeys(ALLOWED_HOSTS + ["127.0.0.1", "localhost", "0.0.0.0"]))

# In local dev, allow all origins by default.
CORS_ALLOW_ALL_ORIGINS = True

# Use console backend by default in dev so local SMTP setup is optional.
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")

# Use MySQL by default in dev (env/secrets). Set USE_SQLITE_FOR_DEV=true to force sqlite.
if os.getenv("USE_SQLITE_FOR_DEV", "false").lower() == "true":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
