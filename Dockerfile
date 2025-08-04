# Multi-stage build for a smaller final image
FROM python:3.11-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.8.3 /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml ./
RUN uv pip install --system --no-cache-dir playwright

# --------------------------------------------------------------------------- #
FROM python:3.11-slim

# Runtime libs needed by Playwright’s headless Chromium
RUN apt-get update && apt-get install -y \
    libnss3 libnspr4 libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libxss1 libxcomposite1 libxdamage1 libxrandr2 libgbm1 \
    libxkbcommon0 libasound2 && rm -rf /var/lib/apt/lists/*

# Copy built site-packages + entrypoints
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

RUN playwright install --with-deps chromium

WORKDIR /app
COPY tools/scrape_website.py ./

# Non-root user
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

ENV PATH="/root/.local/bin/:$PATH"

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import playwright; print('OK')" || exit 1

CMD ["python", "scrape_website.py"]
