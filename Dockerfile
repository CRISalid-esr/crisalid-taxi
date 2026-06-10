FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /code

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy dependency files and README (required by hatchling build)
COPY pyproject.toml uv.lock README.md ./

# Install dependencies using uv (frozen from lockfile)
RUN uv sync --frozen --no-dev

COPY ./app /code/app
COPY ./tests /code/tests

# Install dev dependencies for tests (separate layer for caching)
RUN uv sync --frozen

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
