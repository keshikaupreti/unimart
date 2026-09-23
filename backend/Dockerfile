# syntax=docker/dockerfile:1
FROM python:3.14-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.9.25 /uv /usr/local/bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/opt/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=config.docker_settings

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

RUN groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --create-home app \
    && mkdir -p /data /media \
    && chown app:app /data /media

COPY --chown=app:app . .
COPY --chmod=755 docker/entrypoint.sh /usr/local/bin/unimart-entrypoint
USER app
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=6 \
    CMD python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:8000/api/categories/', timeout=4)"

ENTRYPOINT ["unimart-entrypoint"]
CMD ["serve"]
