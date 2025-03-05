FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONHTTPSVERIFY=0

# Set working directory
WORKDIR /

# Install system dependencies for SSL and certificates
RUN apt-get update && apt-get install -y \
    ca-certificates \
    curl \
    && update-ca-certificates \
    && apt-get clean

# Copy and install dependencies
COPY requirements.txt .
RUN python -m pip install --upgrade pip && \
    python -m pip install --no-cache-dir --trusted-host pypi.org \
    --trusted-host pypi.python.org --trusted-host files.pythonhosted.org \
    -r requirements.txt

# Copy application files
COPY . .

# Ensure start.sh has execution permissions
RUN chmod +x ./start.sh

# Default command
CMD ["./start.sh"]
