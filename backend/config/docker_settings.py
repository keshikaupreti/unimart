"""Local Compose settings; ordinary manage.py commands still use settings.py."""

from .settings import *  # noqa: F403

ALLOWED_HOSTS = ["backend", "localhost", "127.0.0.1", "[::1]"]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "/data/db.sqlite3",
    }
}
MEDIA_ROOT = "/media"
