# ---------------------------------------------------------------------
# ACEest Fitness & Gym - Dockerfile
# Multi-stage build kept intentionally slim for size + security:
#   * python:3.12-slim base (small attack surface, no build toolchain)
#   * dependencies installed before app code copy -> better layer cache
#   * runs as a non-root user
#   * no dev/test dependencies baked into the final image
# ---------------------------------------------------------------------
FROM python:3.12-slim

# Prevent .pyc files and force stdout/stderr to be unbuffered (better
# for container logs).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install only production dependencies first so this layer is cached
# whenever app source (but not requirements.txt) changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the application source.
COPY app.py .

# Create and switch to a non-root user (security best practice).
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/')" || exit 1

# gunicorn is used in production for a proper WSGI server instead of
# Flask's built-in dev server.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
