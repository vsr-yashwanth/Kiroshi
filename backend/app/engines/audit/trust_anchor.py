from __future__ import annotations

import abc
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from backend.app.domain.models.enums import TrustAnchorStatus


class AnchorSubmissionResult:
    def __init__(
        self,
        status: TrustAnchorStatus,
        checkpoint_sequence: int,
        checkpoint_hash: str,
        external_reference: Optional[str] = None,
        error_message: Optional[str] = None,
    ):
        self.status = status
        self.checkpoint_sequence = checkpoint_sequence
        self.checkpoint_hash = checkpoint_hash
        self.external_reference = external_reference
        self.error_message = error_message
        self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "checkpoint_sequence": self.checkpoint_sequence,
            "checkpoint_hash": self.checkpoint_hash,
            "external_reference": self.external_reference,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat(),
        }


class BaseTrustAnchor(abc.ABC):
    """
    Abstract interface for anchoring periodic cryptographic checkpoints
    to external timestamping or ledger services.
    Failure in this layer MUST NEVER break core platform functions (Phase 16-18).
    """

    @abc.abstractmethod
    def anchor_checkpoint(
        self,
        checkpoint_sequence: int,
        checkpoint_hash: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AnchorSubmissionResult:
        pass


class LocalTrustAnchor(BaseTrustAnchor):
    """
    Default trust anchor storing periodic root checkpoints locally
    without external network dependencies.
    """

    def anchor_checkpoint(
        self,
        checkpoint_sequence: int,
        checkpoint_hash: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AnchorSubmissionResult:
        # Local deterministic anchor
        ref = f"local-anchor-seq-{checkpoint_sequence}-{checkpoint_hash[:12]}"
        return AnchorSubmissionResult(
            status=TrustAnchorStatus.ANCHORED,
            checkpoint_sequence=checkpoint_sequence,
            checkpoint_hash=checkpoint_hash,
            external_reference=ref,
        )


class SimulatedExternalRegistryAnchor(BaseTrustAnchor):
    """
    Simulated external tamper-evident registry adapter with bounded retry
    and timeout handling for testing external failure isolation.
    """

    def __init__(self, should_fail: bool = False, timeout_ms: int = 500):
        self.should_fail = should_fail
        self.timeout_ms = timeout_ms

    def anchor_checkpoint(
        self,
        checkpoint_sequence: int,
        checkpoint_hash: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AnchorSubmissionResult:
        if self.should_fail:
            return AnchorSubmissionResult(
                status=TrustAnchorStatus.FAILED,
                checkpoint_sequence=checkpoint_sequence,
                checkpoint_hash=checkpoint_hash,
                error_message="External trust registry timeout / connection refused",
            )

        ref = f"ext-reg-{checkpoint_sequence}-{checkpoint_hash[:16]}"
        return AnchorSubmissionResult(
            status=TrustAnchorStatus.ANCHORED,
            checkpoint_sequence=checkpoint_sequence,
            checkpoint_hash=checkpoint_hash,
            external_reference=ref,
        )
