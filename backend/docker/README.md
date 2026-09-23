# Run both apps with Docker Compose

From the `backend` directory, with Docker Desktop running:

```sh
docker compose up --build -d --wait
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/listings/
- Django admin: http://localhost:8000/admin/
- WebSocket chat: `ws://localhost:8000/ws/conversations/<UUID>/?token=<access token>`

This is a local development/demo setup. It retains Django's debug mode and single-process in-memory chat layer. The frontend runs its compiled standalone server. Both containers run as non-root users, and published ports bind to your computer's loopback interface.

The backend checks configuration and applies migrations before serving requests. The frontend starts after the backend healthcheck passes. Its healthcheck checks both the homepage and an API request through the proxy.

## First use

Containers start with a fresh SQLite database. Your existing `backend/db.sqlite3` and `backend/media/` are excluded from the images and are not modified or automatically imported.

Create an administrator:

```sh
docker compose exec backend python manage.py createsuperuser
```

Then use Django admin to add categories and active meetup locations. Register buyer/seller accounts through the frontend to demonstrate transactions.

Named volumes `backend_data` and `backend_media` persist the database and uploads across container replacement. Normal shutdown keeps them:

```sh
docker compose down
```

`docker compose down --volumes` also deletes the container database and uploaded files. Use it only when you intentionally want to reset the container data.

## Checks

```sh
docker compose config --quiet
docker compose ps
docker compose exec -T backend python manage.py check
docker compose exec -T backend python manage.py makemigrations --check --dry-run
docker compose exec -T backend python manage.py test --noinput
docker compose exec -T backend python docker/smoke_test.py
```

The smoke check goes through the frontend container to verify authentication, listing creation, image upload/media retrieval, purchases, reviews, disputes, and reports. It creates uniquely named temporary users, a category, a meetup location, and a listing, then removes those records and the uploaded file. The Django suite uses a separate test database.

Use `docker compose logs -f` to inspect startup/runtime errors. Source files are copied into the images; after changing code, rerun `docker compose up --build -d --wait`.

If ports 3000 or 8000 are occupied, set different host ports:

```sh
FRONTEND_PORT=13000 BACKEND_PORT=18000 docker compose up --build -d --wait
```

Internal service ports remain 3000 and 8000. Next.js bakes API rewrites into the build, so Compose supplies `BACKEND_URL=http://backend:8000` as a **build argument**. Changing the destination requires rebuilding the frontend image.

## Files

- `backend/compose.yaml`: starts both services, defines healthchecks and persistent volumes.
- `backend/Dockerfile`, `.dockerignore`, `docker/entrypoint.sh`: Python image with dependencies from `uv.lock`.
- `backend/config/docker_settings.py`: container-specific database/media locations and allowed service hosts; local `config/settings.py` is unchanged.
- `frontend/Dockerfile`, `.dockerignore`: multi-stage Node build from `package-lock.json`, with only standalone runtime output copied to the final image.

References: [Compose startup ordering](https://docs.docker.com/compose/how-tos/startup-order/) and [uv Docker integration](https://docs.astral.sh/uv/guides/integration/docker/).

## Verified on 21 September 2026

- Both Linux images built successfully on this machine (ARM64).
- Both services started and passed their healthchecks on ports 3000 and 8000.
- All 20 backend tests passed inside the backend container, including WebSocket chat tests.
- Migration consistency check reported no changes.
- The Compose-network smoke check passed, including authentication, image upload/media retrieval, purchases, reviews, disputes, and reports; its temporary data was removed.
- Chrome loaded the containerized homepage, connected to its API, and opened the interactive login form without browser JavaScript errors.

The services were left running for local use. These checks validate the local container setup; they do not assess a public hosting environment or multi-container scaling of the chat layer.
