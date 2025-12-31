# Multi-stage build for Python FastAPI backend
FROM python:3.13-slim AS builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    zlib1g-dev \
    libjpeg-dev \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY ./app ./app

# Copy utility scripts
COPY ./scripts ./scripts

# Copy configuration files
COPY ./config ./config

# Copy Alembic configuration and migrations
COPY alembic.ini .
COPY ./alembic ./alembic

# Create data directory
RUN mkdir -p /data/uploads /data/processed

# Optional: GeoIP2 database for IP geolocation
# To enable IP geolocation, place GeoLite2-City.mmdb at /app/GeoLite2-City.mmdb
# See docs/GEOIP_SETUP.md for download and setup instructions
# The application will work without this file (location will show as "Unknown location")

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health', timeout=5.0)" || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
