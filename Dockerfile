FROM ghcr.io/astral-sh/uv:python3.12-trixie-slim

RUN useradd -m appuser

WORKDIR /app
RUN chown -R appuser:appuser /app

USER appuser

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_TOOL_BIN_DIR=/usr/local/bin
ENV PYTHONUNBUFFERED=1

RUN --mount=type=cache,target=/home/appuser/.cache/uv,uid=1000,gid=1000 \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

COPY --chown=appuser:appuser . /app

RUN --mount=type=cache,target=/home/appuser/.cache/uv,uid=1000,gid=1000 \
    uv sync --locked --no-dev

ENV PATH="/app/.venv/bin:$PATH"

# CMD ["uv", "run", "manage.py", "runserver", "0.0.0.0:8000"]
# CMD ["uv", "run", "gunicorn", "website.wsgi:application", "--bind", "0.0.0.0:8000"]
