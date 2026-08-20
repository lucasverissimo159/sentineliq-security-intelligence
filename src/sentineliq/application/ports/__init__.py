"""Ports: abstract boundaries the application layer depends on.

Every external system (database, object storage, AI provider) is
represented here as an abstract contract. Concrete implementations
live in `sentineliq.infrastructure` and are wired in at startup via
`sentineliq.interfaces.api.dependencies`. This is the "hexagon" in
hexagonal architecture: application logic never imports a concrete
adapter directly.
"""
from sentineliq.application.ports.ai_analysis import AIAnalysisPort
from sentineliq.application.ports.alert_repository import AlertRepositoryPort
from sentineliq.application.ports.log_repository import LogRepositoryPort
from sentineliq.application.ports.object_storage import ObjectStoragePort

__all__ = [
    "LogRepositoryPort",
    "AlertRepositoryPort",
    "ObjectStoragePort",
    "AIAnalysisPort",
]
