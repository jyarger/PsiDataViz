FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HOST=0.0.0.0 \
    PORT=8050 \
    MOLVIZ_CACHE_DIR=/data/cache

WORKDIR /app

# Install dependencies first (better layer caching), then the package.
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install ".[app]"

RUN mkdir -p /data/cache
EXPOSE 8050

# Serve the Flask WSGI object behind gunicorn (production server).
CMD ["gunicorn", "molviz.app.server:server", \
     "--bind", "0.0.0.0:8050", \
     "--workers", "2", "--threads", "4", "--timeout", "120"]
