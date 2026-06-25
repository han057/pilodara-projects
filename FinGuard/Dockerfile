# Dockerfile
# FinGuard — Multi-Agent Financial Risk Analysis System
#
# Build:   docker build -t finguard .
# Run:     docker-compose up
#
# Note: Ollama runs as a separate service in docker-compose.yml
#       The LLM models are downloaded on first startup.

FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies required by unstructured and lxml
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libxml2-dev \
    libxslt-dev \
    libmagic1 \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p data/chroma_db docs

# Expose FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command — run FastAPI server
CMD ["python", "main.py"]
