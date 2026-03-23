# idachser.blog

Source code of my personal Django-powered blog - https://idachser.com/.

It has:
- markdown posts
- code highlighting and math support (`mdx_math` + MathJax)
- tags
- RSS ('/rss/')
- media uploads (with image compression)

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

Production deploys now pull a prebuilt image for `web` from GHCR. By default the
compose file uses:

```bash
ghcr.io/idachser/idachser.blog:latest
```

## Tests

```bash
uv run manage.py test
```

Tests use SQLite automatically, so they do not require the local PostgreSQL service configuration.

## CI/CD

GitHub Actions now provides:
- CI on every pull request and push to `main`
- production image publishing to GHCR on pushes to `main`
- automatic production deployment over SSH after tests and image publish succeed

### CI behavior

The CI workflow:
- installs Python 3.12 and `uv`
- installs dependencies from `uv.lock`
- runs `uv run manage.py test`
- runs `uv run manage.py check`

### CD behavior

The deploy workflow:
- builds the Docker image from `Dockerfile`
- publishes `latest` and a commit SHA tag to `ghcr.io/idachser/idachser.blog`
- SSHes into the production server
- logs into GHCR on the server
- pulls the exact SHA-tagged image
- restarts `web` and `nginx` with Docker Compose
- runs a smoke check against `https://idachser.com/`

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
- install Docker Compose
- verify the server user can run `docker compose`
- verify GHCR pull access works with the credentials stored in GitHub

Local development stays unchanged and continues to use `docker-compose-test.yaml`.
