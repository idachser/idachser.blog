# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Django 5.2 personal blog (`idachser.blog`) deployed at https://idachser.com/. Uses PostgreSQL in production, SQLite for tests. Dependency management via `uv`. Containerized with Docker + Gunicorn + Nginx + Certbot.

## Common Commands

```bash
# Dependencies
uv sync                        # install deps
uv sync --group dev            # include dev tools (ruff)

# Local dev (native)
export PGSERVICEFILE="$(pwd)/.pg_service.conf"
export PASSFILE="$(pwd)/.website_pgpass"
uv run manage.py migrate
uv run manage.py runserver

# Tests (uses SQLite, no Postgres needed)
uv run manage.py test              # full suite
uv run manage.py test blog.tests   # single app
uv run manage.py check             # Django system checks

# Linting (run after every Python file edit)
uv run ruff format <file_path>
uv run ruff check --fix <file_path>

# Local Docker stack
docker compose -f docker-compose-test.yaml up --build -d
docker compose -f docker-compose-test.yaml exec web uv run manage.py migrate
docker compose -f docker-compose-test.yaml down
```

## Architecture

**Django apps:**
- `website/` — project config: settings, root URLs, WSGI/ASGI, shared context processors
- `blog/` — core domain: `Post`, `Tag`, `PostMedia` models, views, admin, migrations, URL routes
- `pages/` — static-content pages (About, News); no domain logic
- `rss/` — RSS syndication feed (`/rss/`)

**Templates:** `templates/<app>/` per app, with `base.html`, `header.html`, `lightbox.html` at root.

**Static/media:** source files in `static/`, collected output in `staticfiles/`, uploads in `uploads/`.

**Post model key fields:** title, slug, body (Markdown), publish_date, language (EN/DE/RU), tags (M2M), media (M2M via `PostMedia`). Markdown rendering supports syntax highlighting (Pygments) and math (mdx_math + MathJax). `PostMedia` compresses images to ≤20 MP on save.

**Production stack (docker-compose.yaml):** `init-perms` → `web` (Gunicorn) + `db` (PostgreSQL 17) + `nginx` + `certbot`. Image built by CI and pushed to GHCR (`ghcr.io/idachser/idachser.blog`). Deploy SSH-pulls the SHA-tagged image and force-recreates containers.

## Coding Conventions

- 4-space indent, `snake_case` for functions/variables, `PascalCase` for models and admin classes
- Keep views thin; push domain logic to models or small helper functions
- Always run `ruff format` and `ruff check --fix` on every Python file you write or modify before moving on
- Line length: 80 chars; double quotes; E501 ignored in ruff config
- Tests use `django.test.TestCase`; name methods `test_<behavior>`; co-locate with their app (`blog/tests.py`, `pages/tests.py`)
- Commit style: Conventional Commits — `feat(scope): ...`, `fix(scope): ...`, `chore(scope): ...`
- Do not add comments describing changes, history, or progress — only describe current state and purpose

## Important Notes

- `docker compose down -v` destroys database volumes — treat as destructive
- Changes to `website/settings.py`, admin URL exposure, or unpublished post access affect production security — review carefully
- After adding significant functionality, update README.md
- Tests must pass before marking a task complete: run → fix → re-run until green
