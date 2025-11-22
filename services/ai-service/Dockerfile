# ===== BUILDER STAGE =====
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt


# ===== RUNTIME STAGE =====
FROM python:3.12-slim

RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

COPY *.py .

USER app

EXPOSE 8011

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8011/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8011"]