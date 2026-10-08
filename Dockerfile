# Dockerfile for CloudGPT Dedicated AI Agent
FROM python:3.12-slim

WORKDIR /app

# Copy project files
COPY . /app

# Expose HTTP port
EXPOSE 8000

# Set environment
ENV PYTHONUNBUFFERED=1

# Start server
CMD ["python", "server.py"]
