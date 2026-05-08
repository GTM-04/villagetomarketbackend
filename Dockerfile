FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy project files
COPY . /app/

# Create necessary directories
RUN mkdir -p /app/media /app/staticfiles /app/logs

# Collect static files (for production)
RUN python manage.py collectstatic --noinput || true

# Expose ports
EXPOSE 8000 8001

# Default command (can be overridden in docker-compose)
CMD ["gunicorn", "config.asgi:application", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120"]
