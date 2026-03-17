# Repository Guidelines

## Project Structure & Module Organization
- `website/` contains project configuration, settings, URL routing, WSGI/ASGI entrypoints, and shared context processors.
- `blog/` implements the main blog domain: models, views, admin registration, migrations, and routes.
- `pages/` holds static-content style pages such as the About page; `rss/` exposes the syndication feed.
- `templates/` stores shared and app-specific Django templates. `static/` contains source CSS, JavaScript, and icons. Uploaded media is stored in `uploads/`, and collected static files go to `staticfiles/`.
- Tests live next to each app in `blog/tests.py` and `pages/tests.py`.

## Build, Test, and Development Commands
- `uv sync` installs Python dependencies into the local virtual environment.
- `export PGSERVICEFILE="$(pwd)/.pg_service.conf"` and `export PASSFILE="$(pwd)/.website_pgpass"` configure local PostgreSQL access.
- `uv run manage.py migrate` applies database migrations.
- `uv run manage.py runserver` starts the local Django dev server.
- `uv run manage.py test` runs the Django test suite.
- `docker compose -f docker-compose-test.yaml up --build -d` starts the local Docker stack; `docker compose up --build -d` starts the production-like stack.

## Coding Style & Naming Conventions
- Follow existing Django and Python conventions: 4-space indentation, `snake_case` for functions/variables, `PascalCase` for models and admin classes.
- Keep views thin and place domain logic on models or small helper functions when complexity grows.
- Match existing template naming: app templates live under `templates/<app>/`.
- No formatter or linter is configured in this repository; keep changes minimal, readable, and consistent with surrounding code.

## Testing Guidelines
- Use Django’s built-in test framework via `django.test.TestCase`.
- Name test methods `test_<behavior>` and keep tests close to the app they cover.
- Add focused tests for model behavior, routing, and view access control when changing those areas.
- Current test files are placeholders, so new feature work should add meaningful regression coverage.

## Commit & Pull Request Guidelines
- Recent commits are short, imperative, and usually lowercase, for example `fix postgres volume` or `add pagination to posts pages`.
- Prefer concise commit subjects that describe the user-visible or technical change; optional prefixes like `feat:` are already used in history.
- Pull requests should state scope, deployment impact, required env changes, and include screenshots for template or styling changes.

## Security & Configuration Tips
- Do not commit real secrets. Keep `.env`, `.website_pgpass`, and database credentials out of shared history.
- Review changes to `website/settings.py`, admin exposure, and unpublished post access carefully; these affect production safety.
