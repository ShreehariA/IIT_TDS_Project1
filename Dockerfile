FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory to root
WORKDIR /

RUN pip install --upgrade pip setuptools wheel

# Install system dependencies required for libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    libffi-dev \
    musl-dev \
    libopenblas-dev \
    sqlite3 \
    libsqlite3-dev \
    libmagic-dev \
    tesseract-ocr \
    curl \
    git \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install Prettier globally
RUN npm install -g prettier

# Copy the FastAPI application code into the container
COPY src /src

# Install uv
RUN pip install uv

# Expose the port that the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uv", "run", "/src/main.py"]
