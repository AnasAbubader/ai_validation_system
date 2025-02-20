# Use PostgreSQL 13
FROM postgres:13

# Environment variables will be set by docker-compose

# Create directory for initialization scripts
RUN mkdir -p /docker-entrypoint-initdb.d

# Copy initialization script
COPY database/docker-entrypoint-initdb.d/init.sql /docker-entrypoint-initdb.d/01-init.sql

# Set proper permissions
RUN chmod +rx /docker-entrypoint-initdb.d/*

# Expose PostgreSQL port (already exposed by base image, but explicit is better)
EXPOSE 5432