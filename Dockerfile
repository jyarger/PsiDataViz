FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HOST=0.0.0.0 \
    PORT=8050 \
    PSIDATA_CACHE_DIR=/data/cache

WORKDIR /app

# Install the library first, then the interim Dash app. The app's `psidata` dependency is already
# satisfied by the local install, so pip won't try to fetch it from PyPI.
COPY packages/psidata ./packages/psidata
RUN pip install ./packages/psidata
COPY apps/psidataviz-dash ./apps/psidataviz-dash
RUN pip install "./apps/psidataviz-dash[app]"

RUN mkdir -p /data/cache
EXPOSE 8050

# Serve the Flask WSGI object behind gunicorn (production server).
CMD ["gunicorn", "psidataviz_dash.server:server", \
     "--bind", "0.0.0.0:8050", \
     "--workers", "2", "--threads", "4", "--timeout", "120"]
