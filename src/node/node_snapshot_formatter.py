# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Dict, Any, Optional
from src.interfaces.node import IPhysicsEngine, INodeSnapshotFormatter


class NodeSnapshotFormatter:
    """
    Constructs standardized telemetry, physics diagnostics, and step reports for traffic nodes.
    Follows Single Responsibility Principle (SRP) by isolating DTO / dict formatting.
    """

    @staticmethod
    def _extract_physics_report(physics_engine: Optional[IPhysicsEngine]) -> Dict[str, Any]:
        """Extracts kinetic state variables from the physics engine."""
        get_snap_fn = getattr(physics_engine, "get_kinetic_snapshot", None) if physics_engine is not None else None
        if not callable(get_snap_fn):
            return {}
        
        kse_snapshot = get_snap_fn()
        if kse_snapshot is None:
            return {}

        return {
            "position": getattr(kse_snapshot, "p", 0.0),
            "velocity": getattr(kse_snapshot, "v", 0.0),
            "acceleration": getattr(kse_snapshot, "a", 0.0),
            "confidence": getattr(kse_snapshot, "confidence", 1.0)
        }

    def format_step_report(
        self,
        source_id: str,
        status: str,
        value: float,
        loss: float,
        embedding: Any,
        is_ready: bool,
        steps: int,
        physics_engine: Optional[IPhysicsEngine] = None
    ) -> Dict[str, Any]:
        """Formats the result dictionary for a successful real-measurement step."""
        return {
            "source_id": source_id,
            "status": status,
            "type": "real",
            "ready": is_ready,
            "loss": loss,
            "embedding": embedding,
            "value": value,
            "physics": self._extract_physics_report(physics_engine),
            "steps": steps
        }

    def format_ghost_report(
        self,
        source_id: str,
        method_used: str,
        value: float,
        embedding: Any,
        fallback_steps: int,
        physics_engine: Optional[IPhysicsEngine] = None
    ) -> Dict[str, Any]:
        """Formats the result dictionary for a synthetic imputation step (sensor dropout)."""
        return {
            "source_id": source_id,
            "status": f"Fallback: {method_used}",
            "type": "synthetic",
            "ready": True,
            "loss": 0.0,
            "embedding": embedding,
            "value": value,
            "physics": self._extract_physics_report(physics_engine),
            "fallback_count": fallback_steps
        }

    def format_rejected_report(
        self,
        source_id: str,
        value: float,
        loss: float = 0.0
    ) -> Dict[str, Any]:
        """Formats the result dictionary for a rejected sensor reading."""
        return {
            "source_id": source_id,
            "status": "Rejected",
            "ready": False,
            "loss": loss,
            "value": value,
            "rejected": True
        }
