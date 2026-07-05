# idachser.blog

Source code of my personal Django-powered blog - https://idachser.com/.

It has:
- markdown posts (in English, German or Russian)
- code highlighting and math support (`mdx_math` + MathJax)
- tags
- RSS ('/rss/')
- media uploads (with image compression)
- error alerting via admin emails

## Stack

- Python 3.12
- Django 5.2
- PostgreSQL
- `uv` for dependencies
- Gunicorn + Nginx + Certbot in Docker production setup

## Run Locally (Docker, recommended)

```bash
docker compose -f docker-compose-test.yaml up --build -d
docker compose -f docker-compose-test.yaml exec web uv run manage.py migrate
docker compose -f docker-compose-test.yaml exec web uv run manage.py createsuperuser
```

Then open `http://localhost:8000`.

Stop:

```bash
docker compose -f docker-compose-test.yaml down
```

## Production Compose

`docker-compose.yaml` starts:
- `web` (migrate + collectstatic + gunicorn)
- `db`
- `nginx`
- `certbot`

```bash
docker compose up -d
```

The `web` service runs a prebuilt image from GHCR
(`ghcr.io/idachser/idachser.blog:latest` by default, overridable via
`WEB_IMAGE`).

## Configuration (.env)

All runtime configuration lives in `.env` in the project root:

- `DJANGO_KEY` — secret key, required when `DJANGO_DEBUG` is off
- `DJANGO_DEBUG` — `True`/`False`, defaults to `False`
- `DJANGO_ALLOWED_HOSTS` — comma-separated, defaults to `127.0.0.1,localhost,web`
- `ADMIN_URL` — admin path, defaults to `admin/`
- `POSTGRES_USER`, `POSTGRES_DB` — consumed by the `db` container
- `PASSFILE` — path to the Postgres passfile

Admin error emails — `EMAIL_HOST` and `ADMIN_EMAIL` must be set together
(or both left unset); production refuses to start on a half-configured pair:

- `ADMIN_EMAIL` — recipient address(es), comma-separated
- `ADMIN_NAME` — recipient name
- `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` — SMTP credentials
- optional: `EMAIL_PORT` (587), `EMAIL_USE_TLS` (`True`), `EMAIL_TIMEOUT` (10),
  `SERVER_EMAIL` (defaults to `EMAIL_HOST_USER`)

Independently of email, errors are written to `logs/site.log`, which sits on
a Docker volume and survives deploys.

## Tests & Linting

```bash
uv run manage.py test
uv run ruff format <files> && uv run ruff check --fix <files>
```

Tests use SQLite automatically, so they do not require the local PostgreSQL service configuration.

## CI/CD

Every push to `main` runs the test suite, builds the Docker image, publishes
it to GHCR (`latest` + commit SHA tags), then deploys over SSH: the server
checks out the deployed commit, pulls the SHA-tagged image, force-recreates
`web` and `nginx`, and the workflow smoke-checks https://idachser.com/.
Details live in `.github/workflows/ci.yml` and `deploy.yml`.

### Required GitHub Environment Secrets

Create a `production` environment in GitHub and configure:
- `PROD_HOST`
- `PROD_PORT`
- `PROD_USER`
- `PROD_SSH_KEY`
- `PROD_SSH_KNOWN_HOSTS`
- `PROD_APP_DIR`
- `GHCR_USERNAME`
- `GHCR_TOKEN`

`GHCR_TOKEN` must be able to pull packages from GHCR on the server. The workflow
uses the built-in `GITHUB_TOKEN` to publish images.

### One-time Server Bootstrap

On the server:
- clone this repository into the path that will be stored in `PROD_APP_DIR`
- place `.env`, `.pg_service.conf`, and `.website_pgpass` in the project root
- create `secrets/db_password` containing the Postgres password
- install Docker Compose and verify the server user can run `docker compose`
- verify GHCR pull access works with the credentials stored in GitHub
