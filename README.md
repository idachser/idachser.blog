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
- `ADMIN_URL` — admin path, required when `DJANGO_DEBUG` is off; defaults to
  `admin/` only for local development and tests. Must end with a trailing
  slash — nginx renders it into its config as `location /${ADMIN_URL}`, so a
  missing slash leaves the prefix guard misaligned with Django's route
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

nginx writes a JSON access log to `logs/nginx/access.json.log` on the host.
Two upstream fields separate who produced a response, which is what alerting
rules need to key on:

| Response | `status` | `upstream_status` | `upstream_connect` |
| --- | --- | --- | --- |
| nginx answered alone (static, 444, 401, 429) | any | empty | empty |
| Gunicorn unreachable | 502 | 502 | `-` |
| the application returned an error | 500 | 500 | a duration |

## Admin Protection

The admin sits behind two nginx layers before any request reaches Django:

- HTTP basic auth (`nginx/.htpasswd`, gitignored, never committed)
- a per-IP rate limit of 30 req/min with a burst of 20, answering `429`

Because `nginx/default.conf.template` is versioned but the admin path is not,
nginx renders its config at container start: the official image runs `envsubst`
over `/etc/nginx/templates/*.template`, substituting only `ADMIN_URL`
(`NGINX_ENVSUBST_FILTER`) so nginx's own `$variables` survive untouched. The
path therefore stays in `.env` and out of git. Compose fails fast if `ADMIN_URL`
is unset, matching Django's own production guard.

Create the password file on the server (`apache2-utils` / `httpd-tools`):

```bash
htpasswd -B -c nginx/.htpasswd <username>
```

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

`web` runs `migrate` and `collectstatic` before Gunicorn binds port 8000, so
for a while after the container starts nginx is up and the application is not.
A TCP healthcheck on `web` reports when Gunicorn is actually listening, and
`docker compose up --wait` holds the deploy step until then — so the smoke
test no longer fires into that window, and a container that never comes up
fails the deploy with its own logs instead of surfacing as a 502.

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
- create `nginx/.htpasswd` with `htpasswd -B -c nginx/.htpasswd <username>`
- install Docker Compose and verify the server user can run `docker compose`
- verify GHCR pull access works with the credentials stored in GitHub
