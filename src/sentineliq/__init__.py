"""SentinelIQ: AI-powered security log intelligence platform.

Architecture: hexagonal / ports & adapters, in four layers:

    domain          Pure business entities and rules. No framework imports.
    application     Use cases orchestrating the domain through abstract ports.
    infrastructure  Concrete adapters: PostgreSQL, AWS S3, Claude (Anthropic).
    interfaces      Transport layer: the FastAPI HTTP API.

Dependencies only ever point inward (interfaces -> infrastructure ->
application -> domain), never outward. This keeps the domain and use
cases fully testable without a database, AWS credentials, or an
Anthropic API key — see tests/unit.
"""

__version__ = "0.1.0"
