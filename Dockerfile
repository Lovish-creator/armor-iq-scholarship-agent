# ============================================================
# ScholarShield AI — Production Dockerfile
# Compatible with Zop.dev, AWS ECS, GCP Cloud Run, Render & Docker
# ============================================================

FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app/ ./app/
COPY frontend/ ./frontend/
COPY mock_portal/ ./mock_portal/
COPY policies/ ./policies/

# Expose server port
EXPOSE 8080 80 3000

# Start FastAPI server using dynamic PORT environment variable
CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
