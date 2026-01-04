FROM python:3.13-slim

# Install dependencies
RUN python3 -m pip install --no-cache-dir requests

# Create non-root user for security
RUN useradd -m -u 1000 sd_user && \
    mkdir -p /shared && \
    chown -R sd_user:sd_user /shared

WORKDIR /app

# Copy application code
COPY sd_updater.py .
RUN chmod +x sd_updater.py

# Switch to non-root user
USER sd_user

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD test -f /shared/targets.json || exit 1

ENTRYPOINT ["python3", "-u", "sd_updater.py"]

