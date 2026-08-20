"""Unit tests for the LogEntry domain entity."""
from __future__ import annotations

from datetime import UTC, datetime

from sentineliq.domain.entities.log_entry import LogEntry
from sentineliq.domain.value_objects.severity import Severity


def test_new_log_entry_gets_a_unique_id():
    first = LogEntry.new("src", "msg", Severity.LOW, datetime.now(UTC))
    second = LogEntry.new("src", "msg", Severity.LOW, datetime.now(UTC))

    assert first.id != second.id


def test_severity_from_string_is_case_insensitive():
    assert Severity.from_string("high") == Severity.HIGH
    assert Severity.from_string("CRITICAL") == Severity.CRITICAL
