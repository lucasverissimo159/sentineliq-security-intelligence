"""Domain layer.

Pure business rules and entities. This package must never import
anything from `sentineliq.application`, `sentineliq.infrastructure` or
`sentineliq.interfaces` — dependencies only ever point inward, toward
the domain, never outward from it.
"""
