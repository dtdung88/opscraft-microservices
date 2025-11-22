##############################
#        BUILDER STAGE       #
##############################
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies only for compiling wheels
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Build dependency wheels for clean installation later
RUN pip install --no-cache-dir --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt


##############################
#       RUNTIME STAGE        #
##############################
FROM python:3.12-slim

# Create non-root user
RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app

# Runtime (not build) OS deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends postgresql-client curl && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies from wheels
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# ---- SAFE COPY (NO RECURSIVE COPY) ----
COPY *.py .
COPY app .

# Run as non-root
USER app

EXPOSE 8007

# --- HEALTHCHECK ---
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8007/ || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8007"]
