"""FastAPI application: HTTP entrypoint into SentinelIQ."""
from sentineliq.interfaces.api.main import create_app

__all__ = ["create_app"]
