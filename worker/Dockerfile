FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

RUN useradd --create-home --uid 10001 appuser
COPY requirements-worker.txt .
RUN pip install --no-cache-dir -r requirements-worker.txt

COPY engispeak/ engispeak/
COPY worker/ worker/
RUN mkdir -p /app/data && chown -R appuser:appuser /app
USER appuser

CMD ["python", "-m", "worker.worker"]
