"""Application layer: use cases orchestrating domain entities through ports.

May depend on `sentineliq.domain`. Must never depend on
`sentineliq.infrastructure` or `sentineliq.interfaces` — those depend
on this layer, not the other way around.
"""
