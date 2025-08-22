# Multi-stage Production Docker Build for AI Agent Orchestration Hub
# Optimized for MLOps deployment with security hardening

FROM python:3.11-slim as builder

# Build metadata
LABEL maintainer="AI Agent Orchestration Hub"
LABEL version="1.0.0"
LABEL description="Production-ready containerized multi-agent AI orchestration system"

# Build-time security and performance optimizations
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies with security updates
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for build process
RUN useradd --create-home --shell /bin/bash --uid 1000 appuser

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip cache purge

# Production stage - minimal and secure
FROM python:3.11-slim as production

# Production environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PATH="/home/appuser/.local/bin:$PATH"

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user with consistent UID
RUN useradd --create-home --shell /bin/bash --uid 1000 appuser

# Copy Python environment from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set working directory and copy application
WORKDIR /app
COPY --chown=appuser:appuser api/ ./api/
COPY --chown=appuser:appuser requirements.txt ./

# Security hardening - remove unnecessary files and set permissions
RUN find /app -type f -name "*.pyc" -delete \
    && find /app -type d -name "__pycache__" -delete \
    && chmod -R 755 /app

# Switch to non-root user
USER appuser

# Health check with proper endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Production-ready startup with proper process management
CMD ["uvicorn", "api.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--access-log", \
     "--log-config", "/dev/null"]
