# Architecture notes

## Why hexagonal instead of MVC

MVC couples the "shape of the data" to the "shape of the UI/API" —
fine for CRUD-heavy apps, awkward here because SentinelIQ has three
genuinely different technologies to coordinate (a relational database,
object storage, and an LLM API) and the business logic (ingest,
analyze, summarize) shouldn't need to know which one it's talking to.

Hexagonal architecture (ports & adapters) solves that by making the
**application layer depend only on abstractions** (`LogRepositoryPort`,
`ObjectStoragePort`, `AIAnalysisPort`, `AlertRepositoryPort`). Concrete
technology choices are adapters plugged in at the edges. The dependency
rule is one-directional:

```
interfaces  ─▶  infrastructure  ─▶  application  ─▶  domain
```

Nothing in `domain/` or `application/` imports FastAPI, SQLAlchemy,
boto3, or the anthropic SDK. Everything in `infrastructure/` and
`interfaces/` is allowed to.

## Where dependency injection happens

All binding of ports to adapters lives in one file:
`src/sentineliq/interfaces/api/dependencies.py`. FastAPI's `Depends()`
mechanism resolves the chain per-request. To add a new adapter (e.g. a
different AI provider), implement the relevant port and change exactly
one function in that file — no other file needs to know.

## Why entities are immutable dataclasses

`LogEntry`, `ThreatAlert`, and `AnalysisReport` are frozen dataclasses.
Log entries are historical facts (an ingested log line never changes
after the fact), and immutability makes the fakes in `tests/conftest.py`
trivially safe to share across assertions. Where state does need to
change (e.g. acknowledging an alert), the entity exposes a method that
returns a new instance (`ThreatAlert.acknowledge()`) rather than
mutating in place.

## Testing strategy

- `tests/unit/` exercises use cases against fakes (`tests/conftest.py`)
  — fast, no I/O, no external services.
- `tests/integration/` boots the real FastAPI app and hits it via
  `httpx.ASGITransport` — currently just `/health`; extend this as
  routes gain real logic worth covering end-to-end.
- Deliberately no tests against a real PostgreSQL/S3/Claude in this
  base — add those (e.g. with `testcontainers`) once the persistence
  and adapter code is being actively modified.
