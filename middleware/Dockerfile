# Use Python 3.9 slim image as base
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies including PostgreSQL client
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY middleware/requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the database module and application code
COPY database /app/database/
COPY middleware/app app/

# Create necessary directories
RUN mkdir -p app/temp_uploads app/verifier_data

# Set environment variables
ENV PYTHONPATH=/app
# Remove the DATABASE_URL from here since it will be set by docker-compose
# ENV DATABASE_URL=postgresql://anas:A1n9a8s9@host.docker.internal/aiaas
ENV RESNET_SERVER_URL=http://resnet_server:8001
ENV JWT_SECRET=olgecebob9YgHZvwpXXxoPoB0IRX/Jl82XN2+cMmnd8=

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]