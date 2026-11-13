## Run with Docker

The full system is packaged as a single Docker Compose application:

- Patient Management API: <http://localhost:8000> (interactive docs at `/docs`)
- Notification & Document API: <http://localhost:8001> (interactive docs at `/docs`)
- MailHog inbox: <http://localhost:8025>
- Patient PostgreSQL: `localhost:5433`
- Notification PostgreSQL: `localhost:5434`

### First-time setup

Docker Desktop (or Docker Engine with the Compose plugin) must be running. Create
the local environment files from the templates, then replace their placeholder
secret values. `INTERNAL_SERVICE_TOKEN` must be identical in both service files:

```sh
cp .env.example .env
cp patient_management/.env.example patient_management/.env
cp notification_document/.env.example notification_document/.env
```

The existing service templates contain the application settings. The Compose file
overrides database hosts and inter-service URLs so containers communicate using
their Docker service names.

### Start the application

```sh
docker compose up --build
```

On each startup, the Patient Management service waits for PostgreSQL and applies
its Alembic migration chain before starting the API. The Notification service
creates its own tables during startup.

For a background run, use `docker compose up --build -d`. Inspect service logs
with `docker compose logs -f`, and stop it with `docker compose down`.

Database data is stored in named Docker volumes. To intentionally remove all
local containers **and** database data, run:

```sh
docker compose down -v
```
