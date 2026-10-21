# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import pytest
import torch
import tempfile
import os

from src.physics.fundamental_diagrams import (
    GreenshieldsDiagram,
    UnderwoodDiagram,
    NewellDaganzoDiagram,
)
from src.physics.kinematics import (
    NonNegativityBoundsConstraint,
    KinematicAccelerationConstraint,
    TemporalSmoothnessConstraint,
)
from src.physics.continuum import (
    ContinuumConservation,
    SpatialGraphConservation,
)
from src.physics.traffic_loss import TrafficPhysicsLoss
from src.infrastructure.safetensors_repository import SafetensorsRepository
from src.strategies.semantic_clustering import CosineSemanticClusterer
from src.models.pino_traffic import PINOTrafficFlow1D
from src.models.pi_dvae_tcn import PIDVAETCN
from src.models.wavelet_ae_occ import WaveletAEOCC
from src.models.neuro_symbolic import NeuroSymbolicModel
from src.models.modernbert import ModernBertSemanticExtractor


class TestFundamentalDiagrams:
    def test_greenshields(self):
        diag = GreenshieldsDiagram()
        k = torch.tensor([0.0, 60.0, 120.0])
        v_free = torch.tensor([60.0, 60.0, 60.0])
        k_jam = torch.tensor([120.0, 120.0, 120.0])
        
        q = diag.compute_flow(k, v_free, k_jam)
        v = diag.compute_speed(k, v_free, k_jam)
        
        assert q.shape == (3,)
        assert v[0].item() == pytest.approx(60.0, rel=1e-3)
        assert v[1].item() == pytest.approx(30.0, rel=1e-3)
        assert v[2].item() == pytest.approx(0.0, rel=1e-3)
        assert q[0].item() == pytest.approx(0.0, rel=1e-3)
        assert q[1].item() == pytest.approx(1800.0, rel=1e-3)
        assert q[2].item() == pytest.approx(0.0, rel=1e-3)

    def test_underwood(self):
        diag = UnderwoodDiagram()
        k = torch.tensor([0.0, 50.0])
        v_free = torch.tensor([60.0, 60.0])
        k_jam = torch.tensor([120.0, 120.0])
        
        q = diag.compute_flow(k, v_free, k_jam)
        assert q.shape == (2,)
        assert q[0].item() == pytest.approx(0.0, rel=1e-3)
        assert q[1].item() > 0.0

    def test_newell_daganzo(self):
        diag = NewellDaganzoDiagram()
        k = torch.tensor([10.0, 60.0, 110.0])
        v_free = torch.tensor([60.0, 60.0, 60.0])
        k_jam = torch.tensor([120.0, 120.0, 120.0])
        
        q = diag.compute_flow(k, v_free, k_jam)
        assert q.shape == (3,)
        assert (q >= 0.0).all()


class TestKinematicConstraints:
    def test_non_negativity_bounds(self):
        constraint = NonNegativityBoundsConstraint()
        positive_state = torch.tensor([1.0, 2.0, 3.0])
        negative_state = torch.tensor([-1.0, -2.0, 3.0])
        
        loss_pos = constraint.compute_residual(positive_state)
        loss_neg = constraint.compute_residual(negative_state)
        
        assert loss_pos.item() == 0.0
        assert loss_neg.item() > 0.0

    def test_kinematic_acceleration(self):
        constraint = KinematicAccelerationConstraint(max_acceleration=5.0, dt=1.0)
        smooth_vel = torch.tensor([[10.0, 12.0, 14.0, 16.0]])  # dv = 2.0 <= 5.0
        harsh_vel = torch.tensor([[10.0, 25.0, 10.0, 35.0]])   # dv = 15.0 > 5.0
        
        loss_smooth = constraint.compute_residual(smooth_vel)
        loss_harsh = constraint.compute_residual(harsh_vel)
        
        assert loss_smooth.item() == 0.0
        assert loss_harsh.item() > 0.0

    def test_temporal_smoothness(self):
        constraint = TemporalSmoothnessConstraint()
        constant_seq = torch.tensor([[5.0, 5.0, 5.0, 5.0]])
        noisy_seq = torch.tensor([[5.0, 15.0, -5.0, 20.0]])
        
        loss_const = constraint.compute_residual(constant_seq)
        loss_noisy = constraint.compute_residual(noisy_seq)
        
        assert loss_const.item() == 0.0
        assert loss_noisy.item() > 0.0


class TestContinuumConservation:
    def test_continuum_conservation(self):
        conservation = ContinuumConservation()
        # q = rho * v -> 100 = 10 * 10
        q = torch.tensor([[100.0, 200.0]])
        v = torch.tensor([[10.0, 20.0]])
        rho = torch.tensor([[10.0, 10.0]])
        
        loss_perfect = conservation.compute_residual(q=q, v=v, rho=rho)
        assert loss_perfect.item() == pytest.approx(0.0, abs=1e-4)

        # Inconsistent
        q_bad = torch.tensor([[500.0, 500.0]])
        loss_bad = conservation.compute_residual(q=q_bad, v=v, rho=rho)
        assert loss_bad.item() > 0.0

    def test_spatial_graph_conservation(self):
        conservation = SpatialGraphConservation()
        flow = torch.tensor([[[100.0], [100.0]]])  # [Batch=1, Nodes=2, Channels=1]
        edge_index = torch.tensor([[0], [1]])      # 0 -> 1
        
        loss = conservation.compute_residual(flow, edge_index)
        assert loss.item() == 0.0

    def test_spatial_graph_conservation_bifurcation(self):
        """Verifies 1000 veh/h splitting into 500 + 500 is not penalized (Kirchhoff Law)."""
        conservation = SpatialGraphConservation()
        # Node 0 (source: 1000), Node 1 (junction: 1000), Node 2 (branch A: 500), Node 3 (branch B: 500)
        # Edges: 0 -> 1 (1000), 1 -> 2 (500), 1 -> 3 (500)
        edge_index = torch.tensor([[0, 1, 1], [1, 2, 3]], dtype=torch.long)
        flow = torch.tensor([[[1000.0], [1000.0], [500.0], [500.0]]])

        loss = conservation.compute_residual(flow, edge_index)
        assert loss.item() == pytest.approx(0.0, abs=1e-5)

    def test_spatial_graph_conservation_convergence(self):
        """Verifies 400 + 600 merging into 1000 veh/h is physically conserved with zero penalty."""
        conservation = SpatialGraphConservation()
        # Node 0 (400), Node 1 (600), Node 2 (junction: 1000), Node 3 (sink: 1000)
        # Edges: 0 -> 2 (400), 1 -> 2 (600), 2 -> 3 (1000)
        edge_index = torch.tensor([[0, 1, 2], [2, 2, 3]], dtype=torch.long)
        flow = torch.tensor([[[400.0], [600.0], [1000.0], [1000.0]]])

        loss = conservation.compute_residual(flow, edge_index)
        assert loss.item() == pytest.approx(0.0, abs=1e-5)

    def test_spatial_graph_conservation_violation_penalty(self):
        """Verifies unphysical loss of flow at junction (1000 in -> 700 out) is strictly penalized."""
        conservation = SpatialGraphConservation()
        edge_index = torch.tensor([[0, 1, 1], [1, 2, 3]], dtype=torch.long)
        # Inflow to junction 1 is 1000, but predicted outflow at junction 1 is 700 (missing 300 veh/h)
        flow = torch.tensor([[[1000.0], [700.0], [500.0], [200.0]]])

        loss = conservation.compute_residual(flow, edge_index)
        assert loss.item() > 0.0
        # Junction 1 has in=1000, out=700 -> discrepancy 300
        assert loss.item() == pytest.approx(300.0, rel=1e-3)

        # Also verifies direct edge flow violation penalty (edge 0 has 1000, edges 1 & 2 sum to 700)
        edge_flow = torch.tensor([[[1000.0], [500.0], [200.0]]])
        loss_edge = conservation.compute_residual(flow, edge_index, edge_flow=edge_flow)
        assert loss_edge.item() == pytest.approx(300.0, rel=1e-3)

    def test_spatial_graph_conservation_direct_edge_flow(self):
        """Verifies evaluation when edge flows are supplied directly."""
        conservation = SpatialGraphConservation()
        edge_index = torch.tensor([[0, 1, 1], [1, 2, 3]], dtype=torch.long)
        # 3 edges: 0->1 (1000), 1->2 (500), 1->3 (500)
        edge_flow = torch.tensor([[[1000.0], [500.0], [500.0]]])
        flow = torch.zeros(1, 4, 1)

        loss = conservation.compute_residual(flow, edge_index, edge_flow=edge_flow)
        assert loss.item() == pytest.approx(0.0, abs=1e-5)

    def test_spatial_graph_conservation_boundary_tolerance(self):
        """Verifies boundary tolerance slacks boundary imbalances."""
        conservation = SpatialGraphConservation(boundary_tolerance=50.0)
        # Simple graph: 0 -> 1 with flow 100
        edge_index = torch.tensor([[0], [1]], dtype=torch.long)
        flow = torch.tensor([[[100.0], [100.0]]])

        # Imbalance at boundary is 100. Slack is 50. Penalty per boundary node = 50
        loss = conservation.compute_residual(flow, edge_index)
        assert loss.item() == pytest.approx(50.0, rel=1e-3)

    def test_spatial_graph_conservation_permeability_slack(self):
        """Verifies internal node permeability slack absorbs trip arrivals/destinations without penalty."""
        # 0 -> 1 -> 2 (Node 1 is internal junction)
        # Inflow to node 1 is 500, outflow is 450 (50 vehicles parked / reached destination)
        edge_index = torch.tensor([[0, 1], [1, 2]], dtype=torch.long)
        flow = torch.tensor([[[500.0], [450.0], [450.0]]])
        
        # With zero slack, penalty is 50.0
        conservation_strict = SpatialGraphConservation(permeability_slack=0.0)
        assert conservation_strict.compute_residual(flow, edge_index).item() == pytest.approx(50.0, rel=1e-3)
        
        # With slack of 50.0, penalty is zero!
        conservation_porous = SpatialGraphConservation(permeability_slack=50.0)
        assert conservation_porous.compute_residual(flow, edge_index).item() == pytest.approx(0.0, abs=1e-5)

        # With slack of 30.0, penalty is only the excess (20.0)
        conservation_partial = SpatialGraphConservation(permeability_slack=30.0)
        assert conservation_partial.compute_residual(flow, edge_index).item() == pytest.approx(20.0, rel=1e-3)


class TestTrafficPhysicsLossEngine:
    def test_integrated_loss_engine(self):
        engine = TrafficPhysicsLoss(max_acceleration=10.0)
        # 3-channel state: [Batch=2, Channels=3 (q, v, rho), SeqLen=24]
        state = torch.ones(2, 3, 24) * 10.0
        state[:, 0, :] = 100.0  # q = 100
        state[:, 1, :] = 10.0   # v = 10
        state[:, 2, :] = 10.0   # rho = 10 -> q = rho * v = 100
        
        losses = engine.compute_losses(state)
        assert "total_physics_loss" in losses
        assert "loss_bounds" in losses
        assert "loss_kinematics" in losses
        assert "loss_smooth" in losses
        assert "loss_conservation" in losses
        assert losses["total_physics_loss"].item() >= 0.0


class TestSafetensorsAndClustering:
    def test_safetensors_repository(self):
        repo = SafetensorsRepository()
        tensors = {"test_tensor": torch.randn(4, 4)}
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.safetensors")
            success = repo.save_tensors(tensors, path)
            assert success is True
            assert os.path.exists(path)
            
            loaded = repo.load_tensors(path)
            assert "test_tensor" in loaded
            assert loaded["test_tensor"].shape == (4, 4)

    def test_cosine_clusterer(self):
        clusterer = CosineSemanticClusterer(similarity_threshold=0.80)
        vec1 = torch.tensor([[1.0, 0.0, 0.0]])
        concept1, is_new1 = clusterer.match_or_create_concept(vec1, ["traffic jam"])
        assert is_new1 is True
        assert concept1 == "Semantic_Concept_1"
        
        # Similar vector -> should match existing concept
        vec2 = torch.tensor([[0.95, 0.05, 0.0]])
        concept2, is_new2 = clusterer.match_or_create_concept(vec2, ["heavy traffic"])
        assert is_new2 is False
        assert concept2 == concept1


class TestModelsRefactoredPINN:
    def test_pino_traffic_flow_with_custom_diagram(self):
        custom_diagram = UnderwoodDiagram()
        model = PINOTrafficFlow1D(in_channels=32, fundamental_diagram=custom_diagram)
        x = torch.randn(2, 5, 32)
        edge_index = torch.tensor([[0, 1], [1, 2]])
        
        refined, metrics = model(x, edge_index=edge_index)
        assert refined.shape == (2, 5, 32)
        assert "physics_residual" in metrics

    def test_pidvae_tcn_with_injected_physics(self):
        engine = TrafficPhysicsLoss(max_acceleration=8.0)
        model = PIDVAETCN(input_channels=3, hidden_channels=16, latent_channels=8, physics_loss_engine=engine)
        x = torch.randn(2, 3, 24).abs()  # positive inputs
        recon, mu, logvar, residuals = model(x, return_physics_residuals=True)
        
        assert recon.shape == (2, 3, 24)
        assert "total_physics_loss" in residuals
