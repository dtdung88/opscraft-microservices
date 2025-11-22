# ===== BUILDER STAGE =====
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies only for compiling wheels
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Build dependency wheels for clean runtime installation
RUN pip install --no-cache-dir --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt


# ===== RUNTIME STAGE =====
FROM python:3.12-slim

# Create non-root user for security
RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app

#  Install only runtime OS dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends postgresql-client curl && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies from wheels built in the builder stage
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# ---- SAFE COPY (NO RECURSIVE COPY) ----
COPY *.py .
COPY app .

# Run container as non-root user
USER app

EXPOSE 8010

# --- HEALTHCHECK ---
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8010/ || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8010"]
