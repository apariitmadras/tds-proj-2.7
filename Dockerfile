# ---------- builder stage ----------------------------------------------------
FROM python:3.11-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.8.3 /uv /uvx /bin/
WORKDIR /app

# Install Python dependencies (Playwright itself; browsers come later)
COPY pyproject.toml ./
RUN uv pip install --system --no-cache-dir playwright

# ---------- runtime stage ----------------------------------------------------
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

WORKDIR /app

# Copy installed site-packages and entrypoints from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Your application code
COPY tools/scrape_website.py ./

# Use non-root user that already exists in the Playwright image
USER pwuser

# Simple health-check: succeeds if Python can import Playwright
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD ["python", "-c", "import playwright, sys; sys.stdout.write('OK')"]

# Default command when the container starts
CMD ["python", "scrape_website.py"]
