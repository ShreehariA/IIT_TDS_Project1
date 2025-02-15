# Use the Alpine-based image with Python 3.9 and Node.js 14
# FROM nikolaik/python-nodejs:python3.9-nodejs14-alpine
# # Set environment variables to prevent Python from writing .pyc files and to buffer stdout and stderr

# Use Debian-based slim Python image
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /src

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
CMD ["uv", "run", "main.py"]