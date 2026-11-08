"""Observability and Audit Telemetry for SRU Assistant (Phase 11).

Provides unique request identification, privacy-preserving audit logging,
and execution metric capture.
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("sru_assistant.telemetry")


def generate_request_id() -> str:
    """Generate a unique tracking identifier for an incoming academic request."""
    return f"req_{uuid.uuid4().hex[:12]}"


@dataclass
class RequestTelemetry:
    """Structured telemetry record capturing request lifecycle metrics."""

    request_id: str
    query_length: int
    retrieval_mode: str
    model_name: str
    retrieval_count: int = 0
    retrieved_documents: List[str] = field(default_factory=list)
    citation_count: int = 0
    is_grounded: bool = True
    has_conflicts: bool = False
    latency_breakdown_ms: Dict[str, float] = field(default_factory=dict)
    total_latency_ms: float = 0.0
    status_code: int = 200
    threat_detected: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Convert telemetry to a JSON-serializable dictionary."""
        return asdict(self)


class ObservabilityLogger:
    """Logs audit and performance telemetry in a secure, privacy-preserving manner."""

    def __init__(self, log_level: int = logging.INFO) -> None:
        self.logger = logger
        self.logger.setLevel(log_level)

    def record_query(self, telemetry: RequestTelemetry) -> None:
        """Write an observability audit record.
        
        Note: The raw user query content is NOT logged to protect student privacy;
        only query length and execution properties are recorded.
        """
        record = telemetry.to_dict()
        if telemetry.error_message:
            self.logger.warning(
                "Request [%s] FAILED - status=%d, threat=%s, error=%s, total_ms=%.2f",
                telemetry.request_id,
                telemetry.status_code,
                telemetry.threat_detected,
                telemetry.error_message,
                telemetry.total_latency_ms,
            )
        else:
            self.logger.info(
                "Request [%s] SUCCESS - mode=%s, retrieved=%d docs, citations=%d, grounded=%s, total_ms=%.2f",
                telemetry.request_id,
                telemetry.retrieval_mode,
                telemetry.retrieval_count,
                telemetry.citation_count,
                telemetry.is_grounded,
                telemetry.total_latency_ms,
            )
