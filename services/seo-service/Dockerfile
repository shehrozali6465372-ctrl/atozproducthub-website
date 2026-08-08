# seo-service — skeleton image (build context: repository root).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    PIP_NO_CACHE_DIR=1

WORKDIR /srv

# Install the shared backend core, then this service (dependency order).
COPY libs/backend-core /srv/libs/backend-core
COPY services/seo-service /srv/services/seo-service
RUN pip install --no-cache-dir /srv/libs/backend-core \\
    && pip install --no-cache-dir /srv/services/seo-service

EXPOSE 8000

CMD ["uvicorn", "atoz_seo_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
