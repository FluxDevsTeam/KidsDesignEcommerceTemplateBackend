# Use Python slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (for PostgreSQL, Pillow, etc.)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install prod requirements (staging mimics prod)
COPY prod-requirements.txt .
RUN pip install --no-cache-dir -r prod-requirements.txt

# Copy project files
COPY . .

# Expose Django dev server port
EXPOSE 8000

# Default command (overridden in docker-compose)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]