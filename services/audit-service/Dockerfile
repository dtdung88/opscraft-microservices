# ===== BUILDER STAGE =====
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies only in builder stage
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Build wheels for faster & clean install later
RUN pip install --no-cache-dir --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt


# ===== RUNTIME STAGE =====
FROM python:3.12-slim



# Create a secure non-root user
RUN addgroup --system app && adduser --system --ingroup app application

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends postgresql-client curl && \
    rm -rf /var/lib/apt/lists/*

# Install dependencies from wheels
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# ---- Copy only necessary application code (SAFE COPY) ----
COPY *.py .
COPY app .
# (Add more COPY lines if your project has routers/, models/, etc.)

# Change to non-root
USER app

EXPOSE 8009

# --- HEALTHCHECK ---
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8009/ || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8009"]
