"""Pydantic DTOs for the /alerts endpoints."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ThreatAlertOut(BaseModel):
    id: UUID
    title: str
    explanation: str
    severity: str
    related_log_ids: list[UUID]
    detected_at: datetime
    acknowledged: bool


class AnalyzeLogsResponse(BaseModel):
    alerts_found: int
    alerts: list[ThreatAlertOut]
