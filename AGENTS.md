# Repository Guidelines

## Project Structure & Module Organization
- `website/` contains project configuration, settings, URL routing, WSGI/ASGI entrypoints, and shared context processors
- `blog/` implements the main blog domain: models, views, admin registration, migrations, and routes
- `pages/` holds static-content style pages such as the About page; `rss/` exposes the syndication feed
- `templates/` stores shared and app-specific Django templates. `static/` contains source CSS, JavaScript, and icons
- Uploaded media is stored in `uploads/`, and collected static files go to `staticfiles/`
- Tests live next to each app like in `blog/tests.py` and `pages/tests.py`

## Architecture Notes
- blog app handles core domain logic
- pages app is static content only
- rss provides feeds

## Build, Test, and Development Commands
- `uv sync` installs Python dependencies into the local virtual environment
- `export PGSERVICEFILE="$(pwd)/.pg_service.conf"` and `export PASSFILE="$(pwd)/.website_pgpass"` configure local PostgreSQL access
- `uv run manage.py migrate` applies database migrations
- `uv run manage.py runserver` starts the local Django dev server
- `uv run manage.py test` runs the Django test suite, `uv run manage.py test blog.tests` run a single test
- `docker compose -f docker-compose-test.yaml up --build -d` starts the local Docker stack; `docker compose up --build -d` starts the production-like stack

## Task Execution Rules
When implementing a task:
1. Read relevant files only (do not scan entire repository unnecessarily)
2. Make minimal, focused changes
3. Prefer editing existing code over creating new abstractions
4. Keep changes consistent with existing patterns

## Execution Loop
For each task:
1. Implement code changes
2. Run tests. If tests fail:
    - analyze failure
    - fix code
    - re-run tests
3. Repeat until all tests pass

## Coding Style & Naming Conventions
- Follow existing Django and Python conventions: 4-space indentation, `snake_case` for functions/variables, `PascalCase` for models and admin classes
- Keep views thin and place domain logic on models or small helper functions when complexity grows
- Match existing template naming: app templates live under `templates/<app>/`
- No formatter or linter is configured in this repository; keep changes minimal, readable, and consistent with surrounding code
- Always format and check Python files with ruff immediately after writing or editing them: `uv run ruff format <file_path>` and `uv run ruff check --fix <file_path>`. Do this for every Python file you create or modify, before moving on to the next step
- Pass explicit file paths to ruff — only the files you actually changed. Never run ruff on whole directories, and never reformat migrations or other generated/untouched files, so the diff stays focused

## Testing Requirements
- Use Django’s built-in test framework via `django.test.TestCase`
- Name test methods `test_<behavior>` and keep tests close to the app they cover
- Add focused tests for model behavior, routing, and view access control when changing those areas
- Tests must pass before task completion

## Commit & Pull Request Guidelines
- Use Conventional Commit-style messages seen in history: `feat: ...`, `feat(scope): ...`, `chore(scope): ...`, `test: ...`
- Keep commits focused and in imperative mood (one logical change per commit where possible)
- Pull requests should state scope, deployment impact, required env changes, and include screenshots for template or styling changes

## Security & Configuration Tips
- Do not commit real secrets. Keep `.env`, `.website_pgpass`, and database credentials out of shared history
- Review changes to `website/settings.py`, admin exposure, and unpublished post access carefully; these affect production safety
- Treat `docker compose down -v` as data-loss operation

## Important Workflow Notes
- Do not add comments that describe changes, progress, or historical modifications. Avoid comments like "new function," "added test," "now we changed this," or "previously used X, now using Y." Comments should only describe the current state and purpose of the code, not its history or evolution.
- After important functionality added, update README.md accordingly.
