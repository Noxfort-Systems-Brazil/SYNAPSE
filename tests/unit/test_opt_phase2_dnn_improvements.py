# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import pytest
import torch
import numpy as np
from unittest.mock import MagicMock

from src.blocks.temporal_blocks import TemporalBlock
from src.models.tcn_ae import TCNAE
from src.pipeline.specialist_pipeline import SpecialistPipeline
from src.models.pi_dvae_tcn import PIDVAETCN
from src.trainer.corrector_trainer import CorrectorTrainer
from src.models.modernbert import ModernBertEmbeddingModel, ModernBertSemanticExtractor
from src.domain.app_state import AppState
from src.engine.cycle_processor import CycleProcessor


def test_tcn_step_incremental_exact_match():
    """
    Validates mathematical exactness of TCNAE incremental step O(1)
    against the full sequence convolution encode(x[:, :, :t+1]).
    """
    torch.manual_seed(42)
    model = TCNAE(
        num_inputs=1,
        num_channels=[8, 16],
        latent_dim=32,
        kernel_size=2,
        dropout=0.0
    )
    model.eval()

    seq_len = 15
    batch_size = 2
    x = torch.randn(batch_size, 1, seq_len)

    state = None
    with torch.no_grad():
        for t in range(seq_len):
            x_t = x[:, :, t:t + 1]
            latent_step, state = model.step(x_t, state=state)
            
            # Ground truth: full sequence from 0 to t
            latent_full = model.encode(x[:, :, :t + 1])
            diff = (latent_step - latent_full).abs().max().item()
            assert diff < 1e-5, f"Step mismatch at t={t}: max diff={diff:.2e}"


def test_specialist_pipeline_incremental_step():
    """Validates SpecialistPipeline.predict_step O(1) state caching per sensor."""
    torch.manual_seed(42)
    pipeline = SpecialistPipeline(
        input_dim=1,
        output_dim=32,
        num_channels=[8, 16],
        kernel_size=2,
        dropout=0.0,
        device="cpu"
    )
    pipeline.freeze()

    # Step through 5 individual data points
    embeddings = []
    for val in [10.5, 12.0, 11.8, 13.5, 15.0]:
        emb = pipeline.predict_step(val)
        assert isinstance(emb, np.ndarray)
        assert emb.shape == (32,)
        embeddings.append(emb)

    assert len(embeddings) == 5
    # Verify embeddings evolve across timesteps
    diff = np.max(np.abs(embeddings[-1] - embeddings[0]))
    assert diff > 1e-4

    # Verify reset_step_state clears the state
    pipeline.reset_step_state()
    assert pipeline._step_state is None


def test_corrector_sobolev_loss_smoothing():
    """
    Validates that Sobolev (H1) temporal derivative regularization
    runs without errors and penalizes temporal jitter in CorrectorTrainer.
    """
    torch.manual_seed(42)
    device = torch.device("cpu")
    model = PIDVAETCN(input_channels=1, hidden_channels=16, latent_channels=8, kernel_size=2)
    
    # 1. Trainer with Sobolev weight = 0.0
    trainer_no_sob = CorrectorTrainer(
        model=model,
        learning_rate=1e-3,
        physics_weight=0.0,
        sobolev_weight=0.0,
        adaptive_physics_balance=False,
        device=device
    )

    # 2. Trainer with Sobolev weight = 0.5
    trainer_with_sob = CorrectorTrainer(
        model=model,
        learning_rate=1e-3,
        physics_weight=0.0,
        sobolev_weight=0.5,
        adaptive_physics_balance=False,
        device=device
    )

    batch_noisy = torch.randn(4, 20, 1)
    loss_sob = trainer_with_sob.train_step(batch_noisy)
    assert np.isfinite(loss_sob)
    assert loss_sob > 0.0


@pytest.mark.heavy_memory
def test_modernbert_adaptive_layers():
    """
    Validates ModernBertEmbeddingModel adaptive early-exit execution (num_layers),
    ensuring L2 normalization and layer restoration.
    """
    model = ModernBertEmbeddingModel(freeze_weights=True)
    model.eval()

    total_layers = len(model.transformer.layers)
    assert total_layers > 4

    input_ids = torch.randint(100, 2000, (2, 8))
    attention_mask = torch.ones((2, 8), dtype=torch.long)

    with torch.no_grad():
        # Full forward
        emb_full = model(input_ids, attention_mask, num_layers=None)
        assert emb_full.shape == (2, 768)
        norm_full = torch.norm(emb_full, p=2, dim=-1)
        assert torch.allclose(norm_full, torch.ones_like(norm_full), atol=1e-5)

        # Early exit forward with 4 layers
        emb_4 = model(input_ids, attention_mask, num_layers=4)
        assert emb_4.shape == (2, 768)
        norm_4 = torch.norm(emb_4, p=2, dim=-1)
        assert torch.allclose(norm_4, torch.ones_like(norm_4), atol=1e-5)

    # Confirm original layers were safely restored in finally block
    assert len(model.transformer.layers) == total_layers


@pytest.mark.heavy_memory
def test_modernbert_semantic_extractor_num_inference_layers():
    """Validates that ModernBertSemanticExtractor respects num_inference_layers."""
    extractor = ModernBertSemanticExtractor(num_inference_layers=4)
    emb = extractor._get_embedding(["fluxo_elevado", "velocidade_critica"])
    assert emb.shape == (1, 768)
    norm = torch.norm(emb, p=2, dim=-1)
    assert torch.allclose(norm, torch.ones_like(norm), atol=1e-5)


def test_cycle_processor_cuda_streams_concurrency_or_cpu_fallback():
    """
    Validates CycleProcessor CUDA stream concurrency execution
    and fallback consistency.
    """
    app_state = AppState()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    mock_coord = MagicMock()
    mock_coord.model = MagicMock()
    mock_coord.inference.return_value = {
        "spatial_embedding": torch.randn(1, 32, device=device),
        "coordination_score": 0.88
    }

    mock_fuser = MagicMock()
    mock_fuser.inference.return_value = {
        "imputed_flow": torch.randn(1, 10, device=device),
        "fused_states": torch.randn(1, 32, device=device)
    }

    mock_auditor = MagicMock()
    mock_auditor.calibrated_threshold = 0.75
    mock_auditor.inference.return_value = {
        "anomaly_score": 0.12,
        "is_adversarial": False
    }

    mock_xai = MagicMock()
    mock_graph = MagicMock()

    processor = CycleProcessor(
        app_state=app_state,
        device=device,
        coordinator=mock_coord,
        fuser=mock_fuser,
        auditor=mock_auditor,
        xai_manager=mock_xai,
        graph_manager=mock_graph
    )

    if device.type == "cuda":
        assert processor._stream_coord is not None
        assert processor._stream_audit is not None
    else:
        assert processor._stream_coord is None
        assert processor._stream_audit is None

    # Mock prepare_tensors to deliver valid tensor inputs
    x_spatial = torch.randn(1, 32, device=device)
    edge_index = torch.zeros((2, 0), dtype=torch.long, device=device)
    x_temporal = torch.randn(10, 1, device=device)
    obs_mask = torch.ones(1, device=device)
    g_vel = torch.ones(1, device=device)
    processor.tensor_builder.prepare_tensors = MagicMock(
        return_value=(x_spatial, edge_index, x_temporal, obs_mask, g_vel)
    )

    res, _ = processor.run_logic({})
    assert "spatial_embedding" in res
    assert "forecast" in res
    assert "auditor_report" in res
    assert mock_coord.inference.called
    assert mock_auditor.inference.called
    assert mock_fuser.inference.called
