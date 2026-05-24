# ==========================================
# Stage 1: Builder (Heavy dependencies)
# ==========================================
FROM python:3.11-alpine AS builder

WORKDIR /build

# Alpine uses apk; install build deps needed to compile Python wheels from source
RUN apk add --no-cache \
        gcc \
        musl-dev \
        python3-dev \
        libffi-dev \
        openssl-dev

COPY requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip tooling first (fixes wheel / jaraco.context CVEs)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Then install app dependencies
RUN pip install --no-cache-dir -r requirements.txt

# ==========================================
# Stage 2: Runtime (Minimal and Secure)
# ==========================================
FROM python:3.11-alpine AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Upgrade system packages to pick up latest security patches
RUN apk update && apk upgrade && rm -rf /var/cache/apk/*

# Create non-root user (BusyBox adduser syntax)
RUN addgroup -S -g 10001 appgroup && \
    adduser -S -u 10001 -G appgroup appuser

# Copy compiled dependencies from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code with correct ownership
COPY --chown=appuser:appgroup . .

USER appuser

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]