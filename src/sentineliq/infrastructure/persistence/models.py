"""SQLAlchemy ORM models.

These are intentionally kept separate from the domain entities in
`sentineliq.domain.entities`. The ORM models describe *how data is
stored*; the domain entities describe *what the data means*. Mapping
between the two happens in the repository adapters, which keeps the
domain layer free of any SQLAlchemy import.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from sentineliq.infrastructure.persistence.database import Base


class LogEntryModel(Base):
    __tablename__ = "log_entries"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    source: Mapped[str] = mapped_column(String(255), index=True)
    raw_message: Mapped[str] = mapped_column(Text)
    severity: Mapped[int] = mapped_column(Integer, index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    log_metadata: Mapped[dict] = mapped_column(JSON, default=dict)


class ThreatAlertModel(Base):
    __tablename__ = "threat_alerts"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    explanation: Mapped[str] = mapped_column(Text)
    severity: Mapped[int] = mapped_column(Integer, index=True)
    related_log_ids: Mapped[list] = mapped_column(JSON, default=list)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)


class AnalysisReportModel(Base):
    __tablename__ = "analysis_reports"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    summary: Mapped[str] = mapped_column(Text)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    alert_ids: Mapped[list] = mapped_column(JSON, default=list)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    s3_object_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
