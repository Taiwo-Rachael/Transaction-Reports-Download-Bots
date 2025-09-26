# Use a lightweight Python base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (with updated font packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-unifont \
    fonts-noto \
    wget \
    xvfb \
    xauth \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
 && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies
COPY requirements.txt /app/requirements.txt

# Install Python dependencies first (so Docker can cache this layer)
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir --timeout=120 -r /app/requirements.txt \
 && playwright install chromium

# Copy application code
COPY . /app

# Expose port and run app
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
