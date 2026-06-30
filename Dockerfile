FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    HOST=0.0.0.0 \
    PORT=5000 \
    APP_ENV=production \
    AUTO_CREATE_DATABASE=false \
    TESSERACT_CMD=/usr/bin/tesseract

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-eng \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

RUN groupadd --gid 10001 ai-studio \
    && useradd --uid 10001 --gid ai-studio --create-home --shell /usr/sbin/nologin ai-studio

COPY --chown=ai-studio:ai-studio . .

RUN mkdir -p /app/uploads /app/logs \
    && chown -R ai-studio:ai-studio /app/uploads /app/logs \
    && chmod +x /app/docker-entrypoint.sh

USER ai-studio

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/api/health/live', timeout=3)" || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["python", "serve.py"]
