# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import pytest
import torch
import numpy as np

from src.models.pi_dvae_tcn import PIDVAETCN
from src.models.pino_traffic import PINOTrafficFlow1D
from src.blocks.feature_blocks import SpectralFeatureExtractor
from src.models.neuro_symbolic import NeuroSymbolicModel
from src.models.itransformer import iTransformer
from src.models.itransformer_lite import iTransformerLite
from src.models.pi_deeponet import PIDeepONet
from src.models.diffusion_gatv2 import DiffusionGATv2
from src.models.gatv2_lite import SpatialGAT
from src.models.wavelet_ae_occ import WaveletAEOCC
from src.models.tcn_ae import TCNAE, TemporalConvNet

from src.agents.corrector_agent import CorrectorAgent
from src.agents.linguist_agent import LinguistAgent
from src.agents.peak_classifier_agent import PeakClassifierAgent
from src.agents.imputer_agent import ImputerAgent
from src.agents.fuser_agent import FuserAgent
from src.agents.auditor_agent import AuditorAgent
from src.utils.batch_inference import BatchInferenceEngine


def test_tf32_flags_enabled():
    """Verifies that TF32 and cuDNN benchmark are enabled when CUDA is available."""
    from src.utils.hardware import configure_hardware_acceleration

    configure_hardware_acceleration()
    if torch.cuda.is_available():
        assert torch.backends.cuda.matmul.allow_tf32 is True
        assert torch.backends.cudnn.allow_tf32 is True
        assert torch.backends.cudnn.benchmark is True


def test_corrector_agent_amp_train_and_inference():
    """Verifies CorrectorAgent (PI-VAE-TCN) runs training and inference with AMP."""
    agent = CorrectorAgent(input_dim=3, hidden_dim=32, latent_dim=16)
    assert hasattr(agent, "scaler")

    # Train step
    batch = np.random.uniform(10.0, 80.0, (4, 16, 3)).astype(np.float32)
    loss = agent.train_step(batch)
    assert isinstance(loss, float)
    assert not np.isnan(loss)
    assert not np.isinf(loss)

    # Inference step
    data_2d = np.random.uniform(10.0, 80.0, (32, 3)).astype(np.float32)
    recon_2d = agent.inference(data_2d)
    assert recon_2d.shape == data_2d.shape
    assert not np.isnan(recon_2d).any()


@pytest.mark.heavy_memory
def test_linguist_agent_amp_train_and_inference():
    """Verifies LinguistAgent (NeuroSymbolic TCN-PINN) runs with AMP and GradScaler."""
    agent = LinguistAgent(learning_rate=1e-4)
    assert hasattr(agent, "scaler")

    # Inference
    result = agent.inference({"text": "Traffic flow is 1200 veh/h at 60 km/h."})
    assert "is_valid" in result
    assert "error_score" in result
    assert "physics_residual" in result
    assert isinstance(result["is_valid"], bool)

    # Train step
    loss = agent.train_step(["Sensor report: speed is 45 km/h with high density."])
    assert isinstance(loss, float)
    assert not np.isnan(loss)
    assert not np.isinf(loss)


def test_imputer_agent_amp_impute():
    """Verifies ImputerAgent (PatchTST) imputation runs with AMP without NaNs."""
    agent = ImputerAgent(feature_dim=2, seq_len=16, d_model=32, n_heads=2, n_layers=1)
    
    data = np.random.uniform(20.0, 60.0, (48, 2)).astype(np.float32)
    data[5:10, 0] = np.nan
    data[20:25, 1] = np.nan

    imputed = agent.impute(data)
    assert imputed.shape == data.shape
    assert not np.isnan(imputed).any()


def test_batch_inference_engine_amp():
    """Verifies BatchInferenceEngine runs with use_amp=True."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    engine = BatchInferenceEngine(device=device, batch_size=16, use_amp=True)

    model = torch.nn.Sequential(
        torch.nn.Linear(4, 16),
        torch.nn.ReLU(),
        torch.nn.Linear(16, 4)
    )

    data = np.random.randn(100, 4).astype(np.float32)
    output = engine.run(model, data, seq_len=8)
    assert output.shape == data.shape
    assert not np.isnan(output).any()


def test_fuser_agent_amp_integration():
    """Verifies FuserAgent executes PINNTrafficFlow and Diffusion with AMP."""
    agent = FuserAgent(num_variates=3, seq_len=12, spatial_dim=16)

    x_temporal = np.random.randn(12, 3).astype(np.float32)
    output = agent.inference({"x_temporal": x_temporal})
    assert output.shape == (3,)
    assert not np.isnan(output).any()


def test_peak_classifier_agent_amp_train_step():
    """Verifies PeakClassifierAgent (iTransformerLite + SpectralFeatureExtractor) runs train_step with AMP."""
    itransformer_config = {
        'num_variates': 2,
        'seq_len': 96,
        'pred_len': 96,
        'e_layers': 1,
        'd_model': 32,
        'learning_rate': 1e-3
    }
    timesnet_config = {
        'enc_in': 1,
        'seq_len': 96,
        'pred_len': 96,
        'e_layers': 1,
        'd_model': 32,
        'd_ff': 128,
        'top_k': 2,
        'learning_rate': 1e-3
    }
    agent = PeakClassifierAgent(
        itransformer_config=itransformer_config,
        timesnet_config=timesnet_config
    )

    x_windows = np.random.randn(16, 96).astype(np.float32)
    y_labels = (np.random.rand(16) > 0.5).astype(np.float32)

    loss = agent.train_step(x_windows, y_labels)
    assert isinstance(loss, float)
    assert not np.isnan(loss)
    assert not np.isinf(loss)


def test_compass_pipeline_amp():
    """Verifies CompassPipeline runs directional semantic scoring with AMP."""
    from src.pipeline.compass_pipeline import CompassPipeline
    from src.domain.entities import DataSource, MapEdge

    pipeline = CompassPipeline()
    edge_a = MapEdge(
        id="edge_1",
        from_node="A",
        to_node="B",
        shape=[(0.0, 0.0), (100.0, 0.0)],
        real_name="Avenida Central Sentido Centro"
    )
    edge_b = MapEdge(
        id="edge_2",
        from_node="B",
        to_node="A",
        shape=[(100.0, 0.0), (0.0, 0.0)],
        real_name="Avenida Central Sentido Bairro"
    )
    source = DataSource(
        id="radar_01",
        name="Radar Av Central Centro",
        connection_string="192.168.1.100"
    )

    result = pipeline.orient_and_reconcile(
        source=source,
        candidate_edges=[edge_a, edge_b]
    )
    assert "orientation" in result
    assert result["primary_edge_id"] in ("edge_1", "edge_2")
    assert result["confidence"] > 0.0
