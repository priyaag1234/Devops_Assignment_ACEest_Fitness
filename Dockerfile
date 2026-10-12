# ==============================================================================
# Dockerfile for ACEest Fitness & Gym Flask Application
# Optimized for size, speed, and security (BITS Pilani DevOps Assignment 1)
# ==============================================================================

# Base image: Official lightweight Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables:
# - PYTHONDONTWRITEBYTECODE: Prevents Python from writing .pyc files to disk
# - PYTHONUNBUFFERED: Keeps Python from buffering stdout and stderr for live logging
# - PORT: Default listening port
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000

# Set container working directory
WORKDIR /app

# Security best practice: Create a non-root user and group
RUN groupadd -r appgroup && useradd -r -g appgroup -d /app -s /sbin/nologin appuser

# Install dependencies in a separate layer to leverage Docker layer caching
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and test files
COPY . /app

# Change ownership of the app directory to the non-root user
RUN chown -R appuser:appgroup /app

# Switch to the non-privileged user for security compliance
USER appuser

# Expose the application port
EXPOSE 5000

# Healthcheck to monitor container runtime availability
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

# Start the Flask web application
CMD ["python", "app.py"]
