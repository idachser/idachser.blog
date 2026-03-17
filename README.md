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

## Run Locally (without Docker)

```bash
uv sync
export PGSERVICEFILE="$(pwd)/.pg_service.conf"
export PASSFILE="$(pwd)/.website_pgpass"
uv run manage.py migrate
uv run manage.py runserver
```

## Production Compose

`docker-compose.yaml` starts:
- `web` (migrate + collectstatic + gunicorn)
- `db`
- `nginx`
- `certbot`

```bash
docker compose up --build -d
```

## Content Workflow

Use admin to:
- create tags
- create posts
- attach media files to posts
- manage About page content

Notes:
- post media is converted to JPEG and downscaled (max 1920x1080)
- About page is intentionally single-record in admin

## Tests

```bash
uv run manage.py test
```

Tests use SQLite automatically, so they do not require the local PostgreSQL service configuration.
