# ============================================================
# ScholarShield AI — Production Dockerfile
# Compatible with Zop.dev, AWS ECS, GCP Cloud Run, Render & Docker
# ============================================================

FROM python:3.11-slim

WORKDIR /app

# Set environment variables (Zop.dev defaults to port 8000)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    HOST=0.0.0.0

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    (pip install --no-cache-dir armoriq-sdk || true)

# Copy complete project codebase
COPY . .

# Expose server ports (8000 for ZopCloud, 8080, 80)
EXPOSE 8000 8080 80 3000

# Start FastAPI server using dynamic PORT environment variable (default 8000)
CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
