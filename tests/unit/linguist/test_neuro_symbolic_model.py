# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import pytest
import torch
import numpy as np
from unittest.mock import MagicMock, patch

from src.models.neuro_symbolic import NeuroSymbolicModel
from src.agents.linguist_agent import LinguistAgent
from src.physics.traffic_loss import TrafficPhysicsLoss
from src.services.knowledge_transfer_service import KnowledgeTransferService


def test_neuro_symbolic_pinn_residuals():
    """Verifies that NeuroSymbolicModel computes differentiable PINN residuals."""
    with patch("src.models.neuro_symbolic.AutoModel.from_pretrained") as MockAutoModel, \
         patch("src.models.neuro_symbolic.AutoConfig.from_pretrained") as MockAutoConfig:

        mock_config = MagicMock()
        mock_config.hidden_size = 64
        MockAutoConfig.return_value = mock_config

        mock_transformer = MagicMock()
        mock_output = MagicMock()
        mock_output.last_hidden_state = torch.randn(2, 5, 64)
        mock_transformer.return_value = mock_output
        MockAutoModel.return_value = mock_transformer

        model = NeuroSymbolicModel(model_name="mock-model", freeze_transformer=True, latent_dim=32)

        input_ids = torch.randint(0, 1000, (2, 5))
        attention_mask = torch.ones((2, 5))

        recon, orig, residuals = model(input_ids, attention_mask, semantic_type="Vehicle Speed")

        assert recon.shape == (2, 5, 64)
        assert orig.shape == (2, 5, 64)
        assert "loss_bounds" in residuals
        assert "loss_kinematics" in residuals
        assert "loss_conservation" in residuals
        assert "total_physics_loss" in residuals
        assert residuals["total_physics_loss"].item() >= 0.0


def test_linguist_agent_train_and_inference_pinn():
    """Verifies that LinguistAgent trains with local convergence loop and runs inference."""
    with patch("src.agents.linguist_agent.AutoTokenizer.from_pretrained") as MockTokenizer, \
         patch("src.models.neuro_symbolic.AutoModel.from_pretrained") as MockAutoModel, \
         patch("src.models.neuro_symbolic.AutoConfig.from_pretrained") as MockAutoConfig:

        mock_config = MagicMock()
        mock_config.hidden_size = 64
        MockAutoConfig.return_value = mock_config

        mock_transformer = MagicMock()
        mock_output = MagicMock()
        mock_output.last_hidden_state = torch.randn(1, 5, 64)
        mock_transformer.return_value = mock_output
        MockAutoModel.return_value = mock_transformer

        mock_tok_inst = MockTokenizer.return_value
        mock_tok_inst.return_value = {
            "input_ids": torch.randint(0, 1000, (1, 5)),
            "attention_mask": torch.ones((1, 5))
        }

        agent = LinguistAgent(model_name="mock-model")

        batch = [10.0, 12.0, 14.0, 15.0, 16.0]
        loss = agent.train_step(batch, epochs=5, semantic_type="Vehicle Speed")
        assert isinstance(loss, float)
        assert loss >= 0.0

        result = agent.inference({"text": "Speed is 50 km/h, flow is 1200 veh/h"}, semantic_type="Vehicle Speed")
        assert "is_valid" in result
        assert "physics_residual" in result
        assert "error_score" in result


def test_modality_conditioned_physics_loss():
    """Verifies that TrafficPhysicsLoss conditions residuals based on modality."""
    loss_engine = TrafficPhysicsLoss()
    state = torch.tensor([[[10.0, 12.0, 15.0]]])

    loss_count = loss_engine.compute_losses(state, semantic_type="Vehicle Count")
    assert "total_physics_loss" in loss_count
    assert loss_count["loss_conservation"].item() == 0.0

    loss_speed = loss_engine.compute_losses(state, semantic_type="Vehicle Speed")
    assert "loss_kinematics" in loss_speed


def test_knowledge_transfer_service_with_warmup():
    """Verifies that KnowledgeTransferService transfers encoder weights and warms up TCN."""
    transfer_service = KnowledgeTransferService()

    mock_linguist = MagicMock()
    mock_encoder = MagicMock()
    mock_state = {"weight": torch.tensor([1.0, 2.0])}
    mock_encoder.state_dict.return_value = mock_state
    mock_linguist.model.ae.encoder = mock_encoder

    mock_specialist = MagicMock()
    mock_specialist.tcn = MagicMock()
    mock_specialist.predict.return_value = np.zeros((32,))

    series = np.array([10.0, 12.0, 14.0, 15.0, 16.0], dtype=np.float32)
    success = transfer_service.transfer(mock_linguist, mock_specialist, data_series=series)

    assert success is True
    mock_specialist.tcn.load_state_dict.assert_called_once_with(mock_state, strict=False)
    mock_specialist.predict.assert_called_once()


def test_neuro_symbolic_transformer_grad_enabled_logic():
    """Verifies that torch.set_grad_enabled is enabled during training (when unfrozen) and disabled during eval or when frozen."""
    class DummyTransformer(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.config = MagicMock(hidden_size=16)
            self.embed = torch.nn.Embedding(32, 16)
            self.last_grad_enabled = None

        def forward(self, input_ids, attention_mask=None):
            self.last_grad_enabled = torch.is_grad_enabled()
            out = MagicMock()
            out.last_hidden_state = self.embed(input_ids)
            return out

    # Case 1: Unfrozen transformer (freeze_transformer=False)
    dummy_unfrozen = DummyTransformer()
    model_unfrozen = NeuroSymbolicModel(
        freeze_transformer=False,
        latent_dim=8,
        transformer=dummy_unfrozen,
    )
    input_ids = torch.randint(0, 32, (2, 4))
    attention_mask = torch.ones((2, 4))

    model_unfrozen.train()
    recon, orig, _ = model_unfrozen(input_ids, attention_mask, return_physics_residuals=False)
    assert dummy_unfrozen.last_grad_enabled is True
    loss = (recon - orig).pow(2).mean()
    loss.backward()
    assert dummy_unfrozen.embed.weight.grad is not None

    model_unfrozen.eval()
    _ = model_unfrozen(input_ids, attention_mask, return_physics_residuals=False)
    assert dummy_unfrozen.last_grad_enabled is False

    # Case 2: Frozen transformer (freeze_transformer=True)
    dummy_frozen = DummyTransformer()
    model_frozen = NeuroSymbolicModel(
        freeze_transformer=True,
        latent_dim=8,
        transformer=dummy_frozen,
    )
    model_frozen.train()
    _ = model_frozen(input_ids, attention_mask, return_physics_residuals=False)
    assert dummy_frozen.last_grad_enabled is False

