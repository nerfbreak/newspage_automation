# Railway Dockerfile for FastAPI + Playwright Chromium (optimized for size)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PLAYWRIGHT_SKIP_BROWSER_GC=1

# Install Chromium system dependencies (minimal set for headless Chrome)
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libxshmfence1 \
    libx11-xcb1 \
    libxfixes3 \
    libexpat1 \
    fonts-liberation \
    libdbus-glib-1-2 \
    libdbus-1-3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for Docker layer caching)
COPY backend/requirements.txt /app/backend/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/backend/requirements.txt

# Install ONLY Chromium (not Firefox/WebKit) - saves ~500MB
RUN playwright install chromium

# Copy the backend source code
COPY backend/ /app/backend/

# Expose the port (Railway sets $PORT env var at runtime)
EXPOSE 8000

# Start uvicorn - Railway sets $PORT automatically
CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
