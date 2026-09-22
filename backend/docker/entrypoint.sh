#!/bin/sh
set -eu

if [ "${1:-}" = "serve" ]; then
    python manage.py check
    python manage.py migrate --noinput
    # One ASGI process preserves the project's in-memory chat channel layer.
    # runserver also serves admin assets and uploaded media for this local demo.
    exec python manage.py runserver 0.0.0.0:8000 --noreload
fi

exec "$@"
