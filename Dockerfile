# --- builder stage unchanged -------------------------------------------------
FROM python:3.11-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.8.3 /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml ./
RUN uv pip install --system --no-cache-dir playwright

# --- runtime stage: swap base image -----------------------------------------
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY tools/scrape_website.py ./

USER pwuser          # already exists in Playwright image
HEALTHCHECK CMD python - <<'PY' || exit 1
import playwright, sys; sys.stdout.write("OK")
PY

CMD ["python", "scrape_website.py"]
