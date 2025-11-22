# ===== BUILDER STAGE =====
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build deps only in builder
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install python packages into a wheelhouse
RUN pip install --no-cache-dir --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt


# ===== RUNTIME STAGE =====
FROM python:3.12-slim

# Create non-root user
RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app

# Install runtime-only OS packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends postgresql-client curl && \
    rm -rf /var/lib/apt/lists/*

# Install wheels from builder
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*

# Copy application code
COPY app .
COPY *.py .

# Switch to non-root
USER app

EXPOSE 8008

# --- HEALTHCHECK ---
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8008/ || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8008"]
