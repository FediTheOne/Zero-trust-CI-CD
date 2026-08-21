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

ARG BUILD_NUMBER=unknown
ARG GIT_COMMIT=unknown
ARG BUILD_TIMESTAMP=unknown

ENV BUILD_NUMBER=${BUILD_NUMBER} \
    GIT_COMMIT=${GIT_COMMIT} \
    BUILD_TIMESTAMP=${BUILD_TIMESTAMP}

# ==========================================
# Stage 2: Runtime (Minimal and Secure)
# ==========================================
FROM python:3.11-alpine AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Upgrade system packages AND system Python tooling
RUN apk update && apk upgrade && \
    pip install --no-cache-dir --upgrade \
        "setuptools>=78.1.1" \
        "msgpack>=1.2.1" \
        pip wheel && \
    rm -rf /var/cache/apk/* /root/.cache/pip

RUN addgroup -S -g 10001 appgroup && \
    adduser -S -u 10001 -G appgroup appuser

COPY --from=builder /opt/venv /opt/venv
COPY --chown=appuser:appgroup . .

RUN rm -rf \
      /usr/local/lib/python3.11/ensurepip \
      /usr/local/lib/python3.11/site-packages/pip \
      /usr/local/lib/python3.11/site-packages/pip-*.dist-info \
      /usr/local/lib/python3.11/site-packages/setuptools \
      /usr/local/lib/python3.11/site-packages/setuptools-*.dist-info \
      /usr/local/lib/python3.11/site-packages/wheel \
      /usr/local/lib/python3.11/site-packages/wheel-*.dist-info \
      /usr/local/lib/python3.11/site-packages/pkg_resources \
      /usr/local/lib/python3.11/site-packages/_distutils_hack \
      /opt/venv/lib/python3.11/ensurepip \
      /opt/venv/lib/python3.11/site-packages/pip \
      /opt/venv/lib/python3.11/site-packages/pip-*.dist-info \
      /opt/venv/lib/python3.11/site-packages/setuptools \
      /opt/venv/lib/python3.11/site-packages/setuptools-*.dist-info \
      /opt/venv/lib/python3.11/site-packages/wheel \
      /opt/venv/lib/python3.11/site-packages/wheel-*.dist-info \
      /opt/venv/lib/python3.11/site-packages/pkg_resources \
      /opt/venv/lib/python3.11/site-packages/_distutils_hack

USER appuser
EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]