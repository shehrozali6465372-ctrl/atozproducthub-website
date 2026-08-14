# AtozProductHub API gateway — M3 backend foundation image.
# Build context is the repository root.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv

# Install the shared backend core first, then the gateway (dependency order).
COPY libs/backend-core /srv/libs/backend-core
COPY apps/api /srv/apps/api
RUN pip install --no-cache-dir /srv/libs/backend-core \
    && pip install --no-cache-dir /srv/apps/api

# Run as a non-root user (M11 production hardening: least privilege).
RUN addgroup --system appuser && adduser --system --ingroup appuser appuser \
    && chown -R appuser:appuser /srv

USER appuser

EXPOSE 8000

CMD ["uvicorn", "atoz_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
