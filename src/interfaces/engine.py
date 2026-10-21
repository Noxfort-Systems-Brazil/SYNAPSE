# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Any, Dict, NamedTuple, Optional, Tuple, Protocol, runtime_checkable

# Lazy/lightweight references
from src.domain.app_state import AppState
from src.managers.graph_manager import GraphManager


class GatingEvaluation(NamedTuple):
    """Result of evaluating source health, quarantine, and readiness."""
    is_frozen: bool
    should_trigger_linguist: bool
    active_local: int
    active_global: int
    has_quarantine: bool


@runtime_checkable
class IGatingPolicy(Protocol):
    """Contract for evaluating data source readiness, quarantine status, and linguist trigger frequency."""
    def evaluate(self, app_state: AppState, cycle_count: int) -> GatingEvaluation: ...


@runtime_checkable
class IForecastImputer(Protocol):
    """Contract for propagating neural forecast predictions to unobserved graph nodes."""
    def impute(self, forecast: Any, snapshot: Dict[str, Any], graph_manager: GraphManager) -> None: ...


@runtime_checkable
class ISnapshotBuilder(Protocol):
    """Contract for gathering the global network state snapshot."""
    def gather_snapshot(self) -> Dict[str, Any]: ...


@runtime_checkable
class ICycleProcessor(Protocol):
    """Contract for executing the neural inference pipeline."""
    def run_logic(self, snapshot: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]: ...


@runtime_checkable
class IInferenceEngine(Protocol):
    """Contract for the real-time neural inference orchestrator."""
    def run_global_cycle(self) -> None: ...
