"""Infrastructure layer: concrete adapters implementing application ports.

May depend on `sentineliq.application` and `sentineliq.domain`. This is
the only layer allowed to import third-party technology SDKs directly
(SQLAlchemy, boto3, anthropic).
"""
