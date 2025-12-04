# Dockerfile
# Base image with Python 3.11 slim for a small runtime footprint.
FROM python:3.11-slim

# Working directory inside container
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Note: default command is provided in docker-compose.yml
