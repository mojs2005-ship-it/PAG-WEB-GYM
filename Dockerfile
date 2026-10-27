# syntax=docker/dockerfile:1

# ---------- Stage 1: build dependencies into a self-contained venv ----------
FROM python:3.12-slim AS builder

WORKDIR /app

# A virtualenv (unlike `pip install --user`) is self-contained and does not
# depend on any user's $HOME being correctly set at runtime, which makes it
# safe to copy wholesale into the non-root runtime stage below.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------- Stage 2: slim runtime image ----------
FROM python:3.12-slim AS runtime

# Create a non-root user to run the app (security best practice)
RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app

# Bring in the fully-populated virtualenv from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy application source
COPY app.py config.py database.py services.py ./
COPY models/ ./models/
COPY blueprints/ ./blueprints/
COPY templates/ ./templates/
COPY static/ ./static/

# Make sure the non-root user owns everything (writes gym.db here at runtime)
RUN chown -R app:app /app

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    DATABASE_PATH=/app/gym.db \
    PORT=5000

USER app

EXPOSE 5000

# Docker marks the container "healthy" only while /api/health answers 200.
# Uses Python's stdlib so the slim image needs no curl.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/api/health' % os.environ.get('PORT','5000'), timeout=3)"

# gunicorn as the production WSGI server. Cloud platforms (Render, Railway...)
# inject $PORT; locally it falls back to 5000 via the ENV above.
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 2 app:app"]
