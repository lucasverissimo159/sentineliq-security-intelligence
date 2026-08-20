"""Pydantic DTOs for the /reports endpoints."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class GenerateReportRequest(BaseModel):
    period_start: datetime
    period_end: datetime


class AnalysisReportOut(BaseModel):
    id: UUID
    summary: str
    period_start: datetime
    period_end: datetime
    alert_ids: list[UUID]
    generated_at: datetime
