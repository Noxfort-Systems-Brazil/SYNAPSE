# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
AFB Domain Models — Typed contracts for the fusion pipeline.

Replaces untyped Dict[str, Any] with concrete dataclasses (ISP compliance).
"""

from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass(frozen=True)
class SensorReading:
    """A single sensor measurement with its trust context."""
    source_id: str
    value: float
    trust_score: float  # From DataSource.confidence_score (local=0.95, global=0.60)


@dataclass(frozen=True)
class FusionResult:
    """
    The output contract of any AFB fusion operation.
    
    Frozen (immutable) — once produced, the result cannot be accidentally modified
    by downstream consumers.
    """
    value: float              # The fused estimate
    strategy: str             # Which strategy produced this ("trimmed_mean", "kalman_lite", etc.)
    confidence: float         # 0.0-1.0, how confident AFB is in this estimate
    source_count: int         # How many sensors contributed
    is_degraded: bool = False # True if AFB couldn't produce a value (should fall to MEH)


# Sentinel for when AFB has no data at all
NO_DATA = FusionResult(
    value=0.0,
    strategy="no_data",
    confidence=0.0,
    source_count=0,
    is_degraded=True,
)
