"""FastAPI routers, one module per resource."""
from sentineliq.interfaces.api.routers import alerts, logs, reports

__all__ = ["logs", "alerts", "reports"]
