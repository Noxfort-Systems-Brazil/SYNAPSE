# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Any, Dict, Optional
import numpy as np
import torch

from src.interfaces.engine import IForecastImputer
from src.managers.graph_manager import GraphManager


class ForecastImputer(IForecastImputer):
    """
    Propagates neural predictions (GNN / PINN / Transformer forecast)
    to unobserved or missing nodes in the graph and snapshot.
    
    SOLID Responsibility:
    - [SRP] Exclusively performs tensor reshaping, array conversion,
      and propagation into unobserved graph node states.
    - [OCP] Different imputation or decay strategies can be implemented
      or subclassed without modifying the InferenceEngine orchestrator.
    """

    @staticmethod
    def _apply_node_prediction(t_node: Any, pred_val: float, update_kse: bool = False) -> None:
        if t_node is None:
            return
        state_obj = getattr(t_node, "state", None)
        if state_obj is not None and getattr(state_obj, "last_value", None) is not None:
            state_obj.last_value = pred_val
        elif getattr(t_node, "last_value", None) is not None:
            try:
                t_node.last_value = pred_val
            except AttributeError:
                pass
        if update_kse:
            kse_obj = getattr(t_node, "kse", None)
            kse_x = getattr(kse_obj, "x", None)
            if kse_x is not None:
                try:
                    kse_x[0, 0] = pred_val
                except Exception:
                    pass

    def impute(
        self,
        forecast: Optional[Any],
        snapshot: Dict[str, Any],
        graph_manager: GraphManager
    ) -> None:
        """
        Extracts forecast values and fills in zero/missing values in snapshot and graph nodes.
        """
        get_ordered_fn = getattr(graph_manager, "get_ordered_node_ids", None)
        if forecast is None or not callable(get_ordered_fn):
            return

        ordered_nodes = get_ordered_fn()
        if not ordered_nodes:
            return

        # Convert forecast tensor/array to a flat 1D numpy array
        if isinstance(forecast, torch.Tensor):
            forecast_arr = forecast.detach().cpu().numpy()
        elif isinstance(forecast, np.ndarray):
            forecast_arr = forecast
        else:
            try:
                forecast_arr = np.array(forecast)
            except Exception:
                return

        forecast_flat = forecast_arr.flatten()

        # Match ordered nodes with predicted variates
        for i, nid in enumerate(ordered_nodes):
            if i >= len(forecast_flat):
                break

            pred_val = float(forecast_flat[i])
            t_node = graph_manager.get_node(nid)

            if nid not in snapshot:
                # Node has no physical sensor; populate as virtual extrapolated node
                snapshot[nid] = {
                    "value": pred_val if pred_val > 0.0 else 0.0,
                    "type": "virtual",
                    "status": "Extrapolated"
                }
                self._apply_node_prediction(t_node, pred_val, update_kse=False)
            else:
                curr_val = float(snapshot[nid].get("value", 0.0))
                node_type = snapshot[nid].get("type")
                node_status = snapshot[nid].get("status")
                is_unobserved = (
                    curr_val <= 0.0
                    or node_type in ("synthetic", "virtual")
                    or node_status in ("Ghost", "Extrapolated", "Synthesized")
                )
                # If current sensor is unobserved and model predicted a valid value (> 0)
                min_valid_pred = 0.0 if curr_val <= 0.0 else 1.0
                if is_unobserved and pred_val > min_valid_pred:
                    snapshot[nid]["value"] = pred_val
                    self._apply_node_prediction(t_node, pred_val, update_kse=True)
