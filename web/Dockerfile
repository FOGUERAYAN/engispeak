# ---- Étape 1 : build des dépendances (wheels) ----
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# ---- Étape 2 : image d'exécution minimale ----
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000
WORKDIR /app

RUN useradd --create-home --uid 10001 appuser
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

COPY engispeak/ engispeak/
COPY web/ web/
COPY resources/ resources/
RUN mkdir -p /app/data && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import os,urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",\"8000\")}/health', timeout=2)" || exit 1

CMD ["sh", "-c", "uvicorn web.app:create_app --factory --host 0.0.0.0 --port ${PORT} --proxy-headers"]
