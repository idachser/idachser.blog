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
docker compose up --build -d
```

## Tests

```bash
uv run manage.py test
```

Tests use SQLite automatically, so they do not require the local PostgreSQL service configuration.
