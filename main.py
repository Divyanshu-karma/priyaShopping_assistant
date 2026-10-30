"""Vercel application entrypoint re-exporting the FastAPI app from backend.app.main."""

from backend.app.main import app

__all__ = ["app"]
