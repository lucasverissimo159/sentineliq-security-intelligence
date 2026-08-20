"""Domain-level exceptions.

These represent business rule violations and are raised by entities or
use cases. They are technology-agnostic: nothing here knows about
HTTP status codes, SQL errors, or AWS exceptions. Translation to
transport-specific errors (e.g. HTTP 404) happens in the interfaces
layer, never here.
"""
from __future__ import annotations


class DomainError(Exception):
    """Base class for all domain errors."""


class LogEntryNotFoundError(DomainError):
    """Raised when a requested log entry does not exist."""

    def __init__(self, log_id: object) -> None:
        super().__init__(f"Log entry not found: {log_id}")
        self.log_id = log_id


class ThreatAlertNotFoundError(DomainError):
    """Raised when a requested threat alert does not exist."""

    def __init__(self, alert_id: object) -> None:
        super().__init__(f"Threat alert not found: {alert_id}")
        self.alert_id = alert_id


class InvalidLogBatchError(DomainError):
    """Raised when a batch of logs submitted for ingestion is invalid (e.g. empty)."""
