"""Interfaces layer: transport-specific entrypoints (currently: an HTTP API).

May depend on `sentineliq.application` and `sentineliq.infrastructure`.
Nothing outside this layer should depend on it — it is the outermost
ring of the hexagon.
"""
