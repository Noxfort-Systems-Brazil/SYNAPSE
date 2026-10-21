# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
from src.interfaces.base import IDeviceMovable


@runtime_checkable
class IPipeline(Protocol):
    """Contract for data ingestion pipelines."""
    def process_packet(self, source_id: str, payload: Any) -> bool: ...
    def is_ready_for_linguist(self, source_id: str) -> bool: ...


@runtime_checkable
class IFusionPipeline(IDeviceMovable, Protocol):
    """Contract for multi-model neural fusion pipelines."""
    def execute(
        self,
        current_history: Any,
        spatial_context: Optional[Any] = None,
        observability_mask: Optional[Any] = None,
        global_velocities: Optional[Any] = None,
        edge_index: Optional[Any] = None
    ) -> Any: ...

    def execute_operator(
        self,
        current_history: Any,
        query_coords: Optional[Any] = None,
        return_physics_residual: bool = False
    ) -> Any: ...


@runtime_checkable
class IAuditorPipeline(IDeviceMovable, Protocol):
    """Contract for anomaly detection and physical-spectral auditing pipeline."""
    def audit(self, input_data: Any) -> Dict[str, Any]: ...


@runtime_checkable
class IImputerPipeline(IDeviceMovable, Protocol):
    """Contract for missing sensor data reconstruction and gap imputation."""
    def reconstruct(self, incomplete_seq: Any, chunk_size: int = 4096) -> Any: ...


@runtime_checkable
class ICorrectorPipeline(IDeviceMovable, Protocol):
    """Contract for physics-informed denoising and golden dataset reconstruction."""
    def correct(self, input_data: Any, batch_size: int = 128) -> Any: ...


@runtime_checkable
class ISpecialistPipeline(IDeviceMovable, Protocol):
    """Contract for temporal convolutional feature extraction and decoding."""
    def predict(self, input_sequence: Any) -> Any: ...
    def compute_loss(self, input_sequence: Any) -> float: ...


@runtime_checkable
class ILinguistPipeline(IDeviceMovable, Protocol):
    """Contract for semantic-physical validation and contradiction detection."""
    def validate(self, input_data: Any) -> Dict[str, Any]: ...
    def calibrate_threshold(self, validation_texts: List[str]) -> None: ...


@runtime_checkable
class ICoordinatorPipeline(IDeviceMovable, Protocol):
    """Contract for spatial graph reasoning and global network embeddings."""
    def forward_pass(self, x: Any, edge_index: Optional[Any] = None) -> Any: ...


@runtime_checkable
class IJuristPipeline(IDeviceMovable, Protocol):
    """Contract for legal-technical traffic reasoning and on-demand SLM pipeline."""
    @property
    def is_loaded(self) -> bool: ...
    def generate(self, context_data: Dict[str, Any], auto_unload: bool = False) -> str: ...
    def generate_report(
        self,
        tensor_data: Dict[str, Any],
        timestamp: str = "",
        locale: str = "pt_BR",
        target: str = "XAI_Attribution",
        auto_unload: bool = True,
        **kwargs: Any
    ) -> str: ...
    def load_resources(self, device: str = "auto", gpu_layers: int = 16) -> None: ...
    def unload_resources(self) -> None: ...


@runtime_checkable
class ICompassPipeline(IDeviceMovable, Protocol):
    """Contract for directional reconciliation and orientation pipeline."""
    def orient_and_reconcile(
        self,
        source: Any,
        candidate_edges: List[Any],
        data_chunk: Optional[List[Any]] = None,
        data_np: Optional[Any] = None,
        semantic_type: Optional[str] = None
    ) -> Dict[str, Any]: ...

