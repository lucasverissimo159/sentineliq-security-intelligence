# Roadmap

This is the working base: domain, application, infrastructure, and
API layers are wired end-to-end and covered by tests, but the feature
set is intentionally minimal. This file is meant to be handed
directly to an agentic coding tool (e.g. Jules AI) as a prioritized
task list — each item is scoped to be a self-contained unit of work.

## 1. Authentication & authorization
- Add API key or JWT-based auth on all `/logs`, `/alerts`, `/reports` routes.
- Introduce a `User`/`ApiKey` domain concept and a matching Postgres table + migration.
- `/health` should remain unauthenticated (used by load balancers / uptime checks).

## 2. Scheduled analysis
- `AnalyzeLogsUseCase` currently only runs when `POST /alerts/analyze` is
  called manually. Wire it to run on a schedule — options, roughly in
  order of operational simplicity:
  - A simple `asyncio` background task started in the FastAPI lifespan.
  - An external scheduler (cron, APScheduler) invoking the endpoint.
  - An AWS Lambda on an EventBridge schedule, calling the use case directly
    (this project's hexagonal structure makes that a thin wrapper, since
    the use case has no FastAPI dependency).

## 3. Alembic migrations
- Generate the first real migration: `alembic revision --autogenerate -m "initial schema"`,
  then review and commit it under `migrations/versions/`.
- `migrations/versions/` is currently empty (models exist, but no migration
  has been generated yet — this is the first thing to run after cloning).

## 4. Log ingestion adapters
- Right now, logs are ingested via `POST /logs` (a human or another
  service pushes JSON). Add real-world source adapters, e.g.:
  - A syslog listener (UDP/TCP) that maps incoming lines to `LogEntry.new(...)`.
  - A CloudWatch Logs subscription (fits naturally alongside the existing
    AWS adapter in `infrastructure/aws/`).
- Each should ultimately call `IngestLogsUseCase.execute(...)` — no new
  application logic needed, just new adapters producing `LogEntry` objects.

## 5. Alert lifecycle
- `ThreatAlert.acknowledge()` already exists on the domain entity, but
  there's no endpoint to call it yet. Add `POST /alerts/{id}/acknowledge`.
- Consider a `dismissed` vs `acknowledged` vs `escalated` state machine
  if the single boolean flag proves too coarse.

## 6. Observability
- Structured logging (the stdlib `logging` call in `interfaces/api/main.py`
  is a placeholder) — consider `structlog` for JSON logs.
- Basic metrics (request counts, analysis latency, Claude token usage)
  — Prometheus via `prometheus-fastapi-instrumentator` is a low-effort start.

## 7. Frontend / dashboard
- The API is headless by design. A small dashboard (alerts feed, log
  volume over time, report history) would make this demoable end-to-end.
  A separate repo/frontend framework is fine — this backend already
  returns clean JSON via Pydantic schemas.

## 8. Report archival
- `AnalysisReport.s3_object_key` exists on the entity but nothing
  populates it yet. After generating a report, archive it to S3 (mirroring
  `IngestLogsUseCase._archive_raw_batch`) and persist the resulting key.
- This also implies adding a `ReportRepositoryPort` + Postgres adapter,
  since reports aren't persisted at all yet (only returned in the
  response).

## 9. Rate limiting & cost control for the Claude adapter
- `ClaudeAnalysisAdapter` calls the API directly with no caching or
  batching. For a real deployment, consider: capping `find_since` window
  size, deduplicating near-identical log lines before sending to the
  model, and a simple token-usage log.

## Non-goals (for now)
- Multi-tenancy — the schema and API assume a single organization's logs.
- Real-time streaming ingestion (Kafka/Kinesis) — batch ingestion via
  `POST /logs` is enough for a portfolio-scale deployment.
