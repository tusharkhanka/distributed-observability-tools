# Multi-stage build for smaller final image
FROM python:3.11-slim as builder

WORKDIR /app

# Install dependencies - copy wheel first, then requirements
COPY distributed_observability_tools-0.1.0-py3-none-any.whl .
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder stage
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Shared middleware removed - now using distributed-observability-tools package
# COPY shared /app/shared

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Expose port
EXPOSE 9003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9003/health || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9003"]
