# =============================================================================
# Microsoft Fabric Casino/Gaming POC - Data Generation Docker Image
# =============================================================================
# Multi-stage build for optimized image size and security
#
# Build: docker build -t fabric-data-generator .
# Run:   docker run -v ./output:/app/output fabric-data-generator --all
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder - Install dependencies with build tools
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS builder

# Set build-time environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && \
    pip install -r /tmp/requirements.txt

# -----------------------------------------------------------------------------
# Stage 2: Runtime - Minimal image for execution
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

# Image metadata
LABEL maintainer="Microsoft Fabric POC Team" \
      version="1.0.0" \
      description="Synthetic data generator for Casino/Gaming POC" \
      org.opencontainers.image.source="https://github.com/your-org/Supercharge_Microsoft_Fabric" \
      org.opencontainers.image.documentation="https://github.com/your-org/Supercharge_Microsoft_Fabric/blob/main/docker/README.md"

# Runtime environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/data_generation \
    # Application configuration
    DATA_OUTPUT_DIR=/app/output \
    DATA_FORMAT=parquet \
    DATA_DAYS=30 \
    # Azure Event Hub (optional - for streaming)
    EVENTHUB_CONNECTION_STRING="" \
    EVENTHUB_NAME=""

# Create non-root user for security
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=appuser:appgroup data_generation/ ./data_generation/
COPY --chown=appuser:appgroup docker/entrypoint.sh ./entrypoint.sh
COPY --chown=appuser:appgroup docker/generate-all.sh ./generate-all.sh

# Make scripts executable
RUN chmod +x ./entrypoint.sh ./generate-all.sh

# Create output directory with proper permissions
RUN mkdir -p /app/output && chown -R appuser:appgroup /app/output

# Switch to non-root user
USER appuser

# Health check - verify Python and generators are working
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.path.insert(0, '/app/data_generation'); from generators import SlotMachineGenerator; print('OK')" || exit 1

# Default volume for data output
VOLUME ["/app/output"]

# Expose no ports by default (data generation is a batch process)
# EXPOSE is only needed if running in streaming mode with HTTP status endpoint

# Entry point with signal handling
ENTRYPOINT ["./entrypoint.sh"]

# Default command - show help
CMD ["--help"]
