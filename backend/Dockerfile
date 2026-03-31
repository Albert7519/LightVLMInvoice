# Stage 1: Builder - Build environment with compilation tools
FROM nvidia/cuda:12.4.1-devel-ubuntu22.04 AS builder

# Install system dependencies for build
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 python3.11-venv python3.11-dev \
    python3-pip git wget curl ca-certificates \
    build-essential pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3.11 as default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

WORKDIR /app/backend

# Copy requirements and install Python dependencies
COPY requirements.txt requirements.lock* ./
RUN python3 -m venv /opt/venv && \
    . /opt/venv/bin/activate && \
    pip install --no-cache-dir --upgrade pip setuptools wheel && \
    if [ -f requirements.lock ]; then \
        pip install --no-cache-dir -r requirements.lock; \
    else \
        pip install --no-cache-dir -r requirements.txt; \
    fi

# Stage 2: Runtime - Minimal image for deployment
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3.11 as default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Copy Python virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app/backend

# Copy application code
COPY . .

# Create uploads directory with proper permissions
RUN mkdir -p uploads logs && chmod 755 uploads logs

# Health check for FastAPI
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8080/docs || exit 1

# Expose port
EXPOSE 8080

# Default command: Run FastAPI
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
