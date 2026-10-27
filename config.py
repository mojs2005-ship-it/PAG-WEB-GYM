"""Centralized application configuration.

All environment-dependent values (secrets, database path, debug flags)
live here instead of being hardcoded in app.py, as they were in the
legacy version. Values are read from environment variables so the same
codebase can run unmodified in development, testing, Docker, and
production simply by changing environment variables.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class Config:
    """Base configuration shared by every environment."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    DATABASE = os.environ.get("DATABASE_PATH", str(BASE_DIR / "gym.db"))
    DEBUG = False
    TESTING = False
    JSON_SORT_KEYS = False

    # Commit currently running, exposed by /api/health so a deploy can be
    # verified. Hosting platforms inject one of these automatically.
    APP_COMMIT = (
        os.environ.get("APP_COMMIT")
        or os.environ.get("RENDER_GIT_COMMIT")
        or os.environ.get("RAILWAY_GIT_COMMIT_SHA")
        or "unknown"
    )


class DevelopmentConfig(Config):
    """Used for local development (python app.py)."""

    DEBUG = True


class TestingConfig(Config):
    """Used by the pytest suite. DATABASE is overridden per-test."""

    TESTING = True
    DATABASE = os.environ.get("DATABASE_PATH", ":memory:")
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Used inside the Docker container / real deployments."""

    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}

DEFAULT_CONFIG_NAME = os.environ.get("FLASK_ENV", "development")
