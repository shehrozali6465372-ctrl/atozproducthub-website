# aios-bridge — skeleton image (build context: repository root).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv

# Install the shared backend core, the bridge, and the frozen AI OS
# contracts (dependency order: backend-core before consumers).
COPY libs/backend-core /srv/libs/backend-core
COPY libs/contracts /srv/libs/contracts
COPY services/aios-bridge /srv/services/aios-bridge
RUN pip install --no-cache-dir /srv/libs/backend-core \
    && pip install --no-cache-dir /srv/services/aios-bridge

# Contract schemas resolve relative to the source layout at /srv.
ENV AIOS_CONTRACTS_DIR=/srv/libs/contracts/aios

EXPOSE 8000

CMD ["uvicorn", "atoz_aios_bridge.main:app", "--host", "0.0.0.0", "--port", "8000"]
