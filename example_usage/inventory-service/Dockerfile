FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy the wheel file from the dist directory
COPY dist/distributed_observability_tools-0.1.0-py3-none-any.whl ./

# Install the package with all optional dependencies
RUN pip install --no-cache-dir distributed_observability_tools-0.1.0-py3-none-any.whl[all]

# Install additional required dependencies
RUN pip install --no-cache-dir fastapi uvicorn pydantic httpx

# Copy service code
COPY example_usage/inventory-service/main.py ./

# Expose port
EXPOSE 9003

# Health check
HEALTHCHECK --interval=15s --timeout=10s --start-period=90s --retries=10 \
  CMD curl -f http://localhost:9003/health || exit 1

# Run service
CMD ["python", "main.py"]
