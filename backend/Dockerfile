FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY pyproject.toml ./
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
COPY scripts ./scripts
RUN pip install --no-cache-dir . && groupadd -r ops && useradd -r -g ops -d /app ops && chown -R ops:ops /app
USER ops
EXPOSE 8000
CMD ["python", "-m", "scripts.container_entrypoint", "serve"]
