# affiliate-service — skeleton image (build context: repository root).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    PIP_NO_CACHE_DIR=1

WORKDIR /srv

# Install the shared backend core, then this service (dependency order).
COPY libs/backend-core /srv/libs/backend-core
COPY services/affiliate-service /srv/services/affiliate-service
RUN pip install --no-cache-dir /srv/libs/backend-core \\
    && pip install --no-cache-dir /srv/services/affiliate-service

EXPOSE 8000

CMD ["uvicorn", "atoz_affiliate_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
