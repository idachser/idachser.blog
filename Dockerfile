FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_TOOL_BIN_DIR=/usr/local/bin
ENV PYTHONUNBUFFERED=1

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

COPY . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

ENV PATH="/app/.venv/bin:$PATH"

# RUN groupadd --system --gid 999 nonroot \
#  && useradd --system --gid 999 --uid 999 --create-home nonroot
# RUN chown -R nonroot:nonroot /app /app/.venv
# 
# USER nonroot

# CMD ["uv", "run", "manage.py", "runserver", "0.0.0.0:8000"]
CMD ["uv", "run", "gunicorn", "website.wsgi:application", "--bind", "0.0.0.0:8000"]
