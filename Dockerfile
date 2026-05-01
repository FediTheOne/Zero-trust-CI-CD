# ==========================================
# Stage 1: Builder (Heavy dependencies)
# ==========================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Install OS-level build dependencies (discarded in final image)
RUN apt-get update && apt-get install -y --no-install-recommends gcc build-essential

#Install Docker client
RUN curl -fsSLO https://get.docker.com/builds/Linux/x86_64/docker-17.04.0-ce.tgz \
  && tar xzvf docker-17.04.0-ce.tgz \
  && mv docker/docker /usr/local/bin \
  && rm -r docker docker-17.04.0-ce.tgz

# Create a virtual environment and install dependencies
COPY requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# ==========================================
# Stage 2: Runtime (Minimal and Secure)
# ==========================================
FROM python:3.11-slim AS runtime

# Security & performance environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# 1. Create a non-root user and group (Least Privilege)
RUN addgroup --system appgroup && adduser --system --group appuser

# 2. Copy ONLY the compiled dependencies from the builder stage
COPY --from=builder /opt/venv /opt/venv

# 3. Copy the actual application code
COPY . .

# 4. Enforce strict ownership
RUN chown -R appuser:appgroup /app

# 5. Drop root privileges immediately
USER appuser

EXPOSE 8080

# 6. Define the execution command
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]