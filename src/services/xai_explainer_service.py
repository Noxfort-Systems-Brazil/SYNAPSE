# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import torch
from typing import Callable, List, Tuple
from captum.attr import IntegratedGradients

from src.interfaces.xai import IXAIExplainer
from src.utils.logging_setup import get_logger

logger = get_logger("XAI.ExplainerService")


class CaptumExplainerService(IXAIExplainer):
    """
    Mathematical Attribution Service leveraging Captum's Integrated Gradients.
    Decoupled from Qt, threading, and higher-level presentation concerns.
    """

    def compute_attributions(
        self,
        model_wrapper: Callable[[torch.Tensor], torch.Tensor],
        input_vector: List[float],
        device: torch.device
    ) -> Tuple[List[float], float]:
        """
        Computes feature attributions and convergence delta using Integrated Gradients.
        """
        input_tensor = torch.tensor([input_vector], dtype=torch.float32, device=device)
        input_tensor.requires_grad = True

        ig = IntegratedGradients(model_wrapper)
        baseline = torch.zeros_like(input_tensor)

        attributions, delta = ig.attribute(
            inputs=input_tensor,
            baselines=baseline,
            return_convergence_delta=True
        )

        attr_list = attributions.cpu().detach().numpy().flatten().tolist()
        item_fn = getattr(delta, "item", None)
        convergence_delta = float(item_fn()) if callable(item_fn) else float(delta)

        return attr_list, convergence_delta
