# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import numpy as np
import torch
from typing import Dict, Any, Optional, Union, Tuple

# Base Agent and Contracts
from src.agents.base_agent import BaseAgent
from src.interfaces.providers import ISensorCalibrator
from src.interfaces.pipelines import IFusionPipeline
from src.services.dynamic_sensor_calibrator import DynamicSensorCalibrator
from src.factories.fuser_model_factory import FuserModelFactory


class FuserAgent(BaseAgent):
    """
    The Fuser Agent ('O Sintetizador Global').
    
    Pure Orchestrator Architecture (SOLID Compliant):
    - Single Responsibility: Coordinates high-level perception inference.
    - Delegations:
      -> Neural GPU/Tensor Execution: IFusionPipeline (src/pipeline/fusion_pipeline.py)
      -> Dynamic Sensor Calibration: ISensorCalibrator (src/services/dynamic_sensor_calibrator.py)
    """

    def __init__(
        self,
        pipeline: Optional[IFusionPipeline] = None,
        calibrator: Optional[ISensorCalibrator] = None,
        num_variates: int = 10,
        seq_len: int = 60,
        pred_len: int = 1,
        d_model: int = 64,
        n_heads: int = 4,
        layers: int = 2,
        spatial_dim: int = 32,
        name: str = "FuserAgent",
        **kwargs: Any
    ):
        """
        Initializes the Pure Fuser Orchestrator with injected services.
        """
        # Resolve Pipeline via Factory if not directly provided (DIP & Backward Compatibility)
        if pipeline is None:
            pipeline = FuserModelFactory.create_fusion_pipeline(
                num_variates=num_variates,
                seq_len=seq_len,
                pred_len=pred_len,
                d_model=d_model,
                n_heads=n_heads,
                layers=layers,
                spatial_dim=spatial_dim
            )

        super().__init__(model=getattr(pipeline, "module_dict", None), name=name)

        self.pipeline: IFusionPipeline = pipeline
        self.calibrator: ISensorCalibrator = calibrator or DynamicSensorCalibrator(num_variates=num_variates)
        self.cached_edge_index: Optional[torch.Tensor] = None
        self.mlops_pipe: Optional[Any] = kwargs.get("mlops_pipe", None)
        self._mlops_process: Optional[Any] = kwargs.get("mlops_process", None)
        self._default_loss: float = 0.008
        self._default_psi: float = 0.012
        self._learning_rate: float = float(kwargs.get("learning_rate", 1e-4))
        self._spatial_dim: int = spatial_dim
        self._trainer: Optional[Any] = kwargs.get("trainer", None)

    @property
    def last_loss(self) -> float:
        if self._mlops_process is not None:
            try:
                return float(self._mlops_process.get_metrics().get("loss", self._default_loss))
            except Exception:
                return self._default_loss
        return self._default_loss

    @last_loss.setter
    def last_loss(self, val: float):
        self._default_loss = float(val)

    @property
    def last_psi(self) -> float:
        if self._mlops_process is not None:
            try:
                return float(self._mlops_process.get_metrics().get("psi", self._default_psi))
            except Exception:
                return self._default_psi
        return self._default_psi

    @last_psi.setter
    def last_psi(self, val: float):
        self._default_psi = float(val)

    def attach_mlops(self, pipe: Any, process: Optional[Any] = None):
        """Attaches unidirectional MLOps pipe and optional background process."""
        self.mlops_pipe = pipe
        self._mlops_process = process

    def get_mlops_metrics(self) -> Dict[str, float]:
        """Returns the current MLOps metrics of the Fuser Agent."""
        return {
            "loss": self.last_loss,
            "drift": self.last_psi,
        }

    def set_topology(self, edge_index: torch.Tensor):
        """Registers active map topology in the orchestrator."""
        self.cached_edge_index = edge_index

    def update_observability(self, active_mask: np.ndarray):
        """Delegates sensor observability state updates to the Calibrator service."""
        self.calibrator.update_observability(active_mask)

    def inference(self, input_data: Dict[str, Any]) -> Union[np.ndarray, Dict[str, Any]]:
        """Unified inference entry point."""
        if "x_temporal" not in input_data:
            raise ValueError("Fuser inference requires 'x_temporal'.")

        exec_op_fn = getattr(self.pipeline, "execute_operator", None)
        if "query_coords" in input_data and callable(exec_op_fn):
            return self.fuse_operator(
                current_history=input_data["x_temporal"],
                query_coords=input_data["query_coords"],
                return_physics_residual=input_data.get("return_physics_residual", False)
            )

        return self.fuse_state(
            current_history=input_data["x_temporal"],
            spatial_context=input_data.get("spatial_context"),
            observability_mask=input_data.get("observability_mask"),
            global_velocities=input_data.get("global_velocities"),
            edge_index=input_data.get("edge_index", self.cached_edge_index),
            edge_attr=input_data.get("edge_attr")
        )

    def fuse_operator(
        self,
        current_history: Union[np.ndarray, torch.Tensor],
        query_coords: Optional[Union[np.ndarray, torch.Tensor]] = None,
        return_physics_residual: bool = False
    ) -> Union[np.ndarray, Tuple[np.ndarray, Dict[str, float]]]:
        """
        Executes continuous Neural Operator inference (PI-DeepONet).
        Maps sparse sensor observations to continuous physical traffic fields [density, speed, flow]
        across arbitrary query coordinates in O(1) time.
        """
        exec_op_fn = getattr(self.pipeline, "execute_operator", None)
        if callable(exec_op_fn):
            return exec_op_fn(
                current_history=current_history,
                query_coords=query_coords,
                return_physics_residual=return_physics_residual
            )
        raise NotImplementedError("Configured pipeline does not support execute_operator.")

    def fuse_state(
        self,
        current_history: Union[np.ndarray, torch.Tensor],
        spatial_context: Optional[torch.Tensor] = None,
        observability_mask: Optional[Any] = None,
        global_velocities: Optional[Any] = None,
        edge_index: Optional[torch.Tensor] = None,
        edge_attr: Optional[torch.Tensor] = None
    ) -> np.ndarray:
        """
        Pure Orchestration Workflow:
        1. Executes neural execution pipeline service (Diffusion -> PINN -> iTransformer).
        2. Applies dynamic bias calibration on ground truth sensors.
        """
        # Step 1: Execute neural pipeline service (GPU tensor processing)
        raw_state = self.pipeline.execute(
            current_history=current_history,
            spatial_context=spatial_context,
            observability_mask=observability_mask,
            global_velocities=global_velocities,
            edge_index=edge_index if edge_index is not None else self.cached_edge_index,
            edge_attr=edge_attr
        )

        # Step 2: Apply dynamic sensor calibration
        calibrated_output = self.calibrator.apply(
            raw_output=raw_state,
            current_history=current_history,
            observability_mask=observability_mask
        )

        # Step 3: Pure Push into MLOps Pipe (Fire-and-Forget, zero blocking)
        if self.mlops_pipe is not None:
            try:
                # Convert target and history from CUDA Tensor / ndarray to 1D CPU NumPy array
                if isinstance(current_history, torch.Tensor):
                    hist_np = current_history.detach().cpu().numpy()
                elif isinstance(current_history, np.ndarray):
                    hist_np = current_history
                else:
                    hist_np = np.asarray(current_history, dtype=np.float32)

                target_np = hist_np[-1] if hist_np.ndim >= 2 else hist_np
                target_np = np.asarray(target_np, dtype=np.float32).flatten()

                # Convert prediction to 1D CPU NumPy array
                if isinstance(calibrated_output, torch.Tensor):
                    pred_np = calibrated_output.detach().cpu().numpy()
                elif isinstance(calibrated_output, np.ndarray):
                    pred_np = calibrated_output
                else:
                    pred_np = np.asarray(calibrated_output, dtype=np.float32)

                if pred_np.ndim >= 2 and pred_np.shape[0] != target_np.shape[0]:
                    pred_np = pred_np[0] if pred_np.shape[1] == target_np.shape[0] else pred_np[-1]
                pred_np = np.asarray(pred_np, dtype=np.float32).flatten()

                # Convert values for drift tracking to 1D CPU NumPy array
                if global_velocities is not None:
                    if isinstance(global_velocities, torch.Tensor):
                        vals_np = global_velocities.detach().cpu().numpy()
                    elif isinstance(global_velocities, np.ndarray):
                        vals_np = global_velocities
                    else:
                        vals_np = np.asarray(global_velocities, dtype=np.float32)
                    vals_np = np.asarray(vals_np, dtype=np.float32).flatten()
                else:
                    vals_np = pred_np

                self.mlops_pipe.push_snapshot({
                    "prediction": pred_np,
                    "target": target_np,
                    "values": vals_np
                })
            except Exception:
                pass

        return calibrated_output

    def predict_state(
        self,
        current_history: np.ndarray,
        spatial_context: Optional[torch.Tensor] = None
    ) -> np.ndarray:
        """Alias for backward compatibility with CycleProcessor."""
        return self.fuse_state(current_history, spatial_context=spatial_context)

    def train_step(self, batch_data: Any) -> float:
        """Delegates training step to FuserTrainer (lazily initialized on first call)."""
        if self._trainer is None:
            from src.trainer.fuser_trainer import FuserTrainer
            comp_model = getattr(self.pipeline, "module_dict", None) or self.model
            if comp_model is None:
                return 0.0
            self._trainer = FuserTrainer(
                composite_model=comp_model,
                learning_rate=self._learning_rate,
                spatial_dim=self._spatial_dim,
            )
        return float(self._trainer.train_step(batch_data, cached_edge_index=self.cached_edge_index))
