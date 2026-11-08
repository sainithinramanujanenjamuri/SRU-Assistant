"""Reliability and Security Layer for SRU Assistant (Phase 11).

Provides query safety, prompt injection detection, document validation,
path traversal defense, integrity checks, and observability telemetry.
"""

from __future__ import annotations

from app.security.document_guard import (
    DocumentGuard,
    DocumentSecurityError,
    DocumentValidationResult,
)
from app.security.query_guard import (
    QueryGuard,
    QueryGuardResult,
    QuerySecurityError,
)
from app.security.telemetry import (
    ObservabilityLogger,
    RequestTelemetry,
    generate_request_id,
)

__all__ = [
    "QueryGuard",
    "QueryGuardResult",
    "QuerySecurityError",
    "DocumentGuard",
    "DocumentValidationResult",
    "DocumentSecurityError",
    "RequestTelemetry",
    "ObservabilityLogger",
    "generate_request_id",
]
