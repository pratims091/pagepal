# Use Python 3.12 as base image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# Set work directory
WORKDIR /app

# Install system dependencies and pipenv
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    python3-dev \
    && apt-get clean \
    # && rm -rf /var/lib/apt/lists/* && \
    pip install --upgrade pip && \
    pip install pipenv

# Copy Pipfile and Pipfile.lock
COPY Pipfile* ./

# Install dependencies
RUN pipenv install --deploy --system

# Copy project
COPY . .

# Create data directory
RUN mkdir -p data/chroma_db && \
    chmod -R 777 data

# Run application
CMD ["python", "-m", "main"]