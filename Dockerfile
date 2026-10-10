# syntax=docker/dockerfile:1
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.12.18 /uv /usr/local/bin/uv
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8080
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --locked --no-dev --no-editable
RUN useradd --uid 10001 --create-home mcp && mkdir /data && chown mcp /data
ENV BLS_DATABASE_PATH=/data/bls_catalog.db
USER mcp
EXPOSE 8080
CMD ["/app/.venv/bin/python", "-m", "bls_escalation_mcp.app"]
