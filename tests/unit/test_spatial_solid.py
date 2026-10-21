# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import pytest
import torch
import numpy as np
from unittest.mock import MagicMock

from src.domain.entities import MapEdge, MapNode
from src.domain.model_contracts import IGraphSampler, ISpatialGraphMutator
from src.services.graph_sampler import BfsGraphSampler
from src.services.spatial_graph_mutator import SpatialGraphMutator
from src.services.line_graph_builder import LineGraphBuilder


@pytest.fixture
def sample_road_network():
    """Builds a small 10-edge grid network for testing."""
    nodes = [
        MapNode(id=f"n{i}", x=float(i % 3) * 100.0, y=float(i // 3) * 100.0, node_type="junction")
        for i in range(9)
    ]
    edges = [
        MapEdge(id="e0", from_node="n0", to_node="n1", shape=[(0.0, 0.0), (100.0, 0.0)], weight=100.0),
        MapEdge(id="e1", from_node="n1", to_node="n2", shape=[(100.0, 0.0), (200.0, 0.0)], weight=100.0),
        MapEdge(id="e2", from_node="n0", to_node="n3", shape=[(0.0, 0.0), (0.0, 100.0)], weight=100.0),
        MapEdge(id="e3", from_node="n1", to_node="n4", shape=[(100.0, 0.0), (100.0, 100.0)], weight=100.0),
        MapEdge(id="e4", from_node="n2", to_node="n5", shape=[(200.0, 0.0), (200.0, 100.0)], weight=100.0),
        MapEdge(id="e5", from_node="n3", to_node="n4", shape=[(0.0, 100.0), (100.0, 100.0)], weight=100.0),
        MapEdge(id="e6", from_node="n4", to_node="n5", shape=[(100.0, 100.0), (200.0, 100.0)], weight=100.0),
        MapEdge(id="e7", from_node="n3", to_node="n6", shape=[(0.0, 100.0), (0.0, 200.0)], weight=100.0),
        MapEdge(id="e8", from_node="n4", to_node="n7", shape=[(100.0, 100.0), (100.0, 200.0)], weight=100.0),
        MapEdge(id="e9", from_node="n5", to_node="n8", shape=[(200.0, 100.0), (200.0, 200.0)], weight=100.0),
        MapEdge(id="e10", from_node="n6", to_node="n7", shape=[(0.0, 200.0), (100.0, 200.0)], weight=100.0),
        MapEdge(id="e11", from_node="n7", to_node="n8", shape=[(100.0, 200.0), (200.0, 200.0)], weight=100.0),
    ]
    return edges, nodes


def test_bfs_graph_sampler_contract_and_expansion(sample_road_network):
    """Test BfsGraphSampler satisfies IGraphSampler and samples connected components."""
    edges, nodes = sample_road_network
    sampler = BfsGraphSampler()
    assert isinstance(sampler, IGraphSampler)

    # Sample a subgraph of 5-8 edges
    sub_edges, sub_nodes = sampler.sample_subgraph(edges, nodes, min_edges=5, max_edges=8)
    assert len(sub_edges) >= 5
    assert len(sub_edges) <= 8
    assert len(sub_nodes) > 0

    # Ensure all sampled edges have their nodes included in sub_nodes
    sub_node_ids = {n.id for n in sub_nodes}
    for e in sub_edges:
        assert e.from_node in sub_node_ids
        assert e.to_node in sub_node_ids


def test_bfs_graph_sampler_edge_cases():
    """Test BfsGraphSampler handles empty or minimal edge collections gracefully."""
    sampler = BfsGraphSampler()
    empty_edges, empty_nodes = sampler.sample_subgraph([], [])
    assert empty_edges == []
    assert empty_nodes == []

    small_edge = [MapEdge(id="e0", from_node="n0", to_node="n1", shape=[(0, 0), (1, 1)])]
    small_node = [MapNode(id="n0", x=0, y=0, node_type="j"), MapNode(id="n1", x=1, y=1, node_type="j")]
    res_edges, res_nodes = sampler.sample_subgraph(small_edge, small_node, min_edges=5)
    assert len(res_edges) == 1
    assert len(res_nodes) == 2


def test_spatial_graph_mutator_contract_and_jitter(sample_road_network):
    """Test SpatialGraphMutator satisfies ISpatialGraphMutator and generates valid mutants."""
    edges, _ = sample_road_network
    mutator = SpatialGraphMutator()
    assert isinstance(mutator, ISpatialGraphMutator)

    mutants, surviving = mutator.mutate(edges, noise_scale=10.0, drop_prob=0.2)

    assert len(mutants) == len(surviving)
    assert len(mutants) >= 3  # Minimum guarantee
    assert len(mutants) <= len(edges)

    for m in mutants:
        assert m.id.startswith("mut_")
        assert len(m.shape) >= 2


def test_spatial_graph_mutator_empty():
    """Test SpatialGraphMutator with empty edge input."""
    mutator = SpatialGraphMutator()
    mutants, surviving = mutator.mutate([])
    assert mutants == []
    assert surviving == []


def test_task_registry_cartographer_retired(sample_road_network):
    """Verify TaskRegistry no longer schedules Cartographer tasks (deterministic map matching)."""
    from src.optimization.task_registry import TaskRegistry

    univ_data = np.random.randn(200, 4).astype(np.float32)

    tasks = TaskRegistry.build_tasks(
        univ_data=univ_data,
        map_graph=None,
        map_file_path="mock_map.net.xml.gz",
        device=torch.device('cpu')
    )

    cart_task = next((t for t in tasks if t.name == "cartographer"), None)
    assert cart_task is None, "Cartographer neural task should be retired from TaskRegistry."


