"""Pydantic DTOs for the /logs endpoints.

Kept separate from domain entities on purpose: request/response shape
is an HTTP concern (e.g. `severity` arrives as a plain string here)
and should be free to evolve independently of the domain model.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LogEntryIn(BaseModel):
    source: str = Field(..., examples=["firewall-edge-01"])
    raw_message: str = Field(..., examples=["Blocked inbound connection from 203.0.113.4:443"])
    severity: str = Field(..., examples=["MEDIUM"])
    occurred_at: datetime
    metadata: dict[str, str] = Field(default_factory=dict)


class LogIngestRequest(BaseModel):
    logs: list[LogEntryIn]


class LogEntryOut(BaseModel):
    id: UUID
    source: str
    raw_message: str
    severity: str
    occurred_at: datetime
    ingested_at: datetime
    metadata: dict[str, str]


class LogIngestResponse(BaseModel):
    ingested: int
    logs: list[LogEntryOut]
