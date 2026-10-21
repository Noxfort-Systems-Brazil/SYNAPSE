# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import pytest
import numpy as np
import torch
from unittest.mock import MagicMock

from src.domain.entities import SourceStatus
from src.engine.gating_policy import SourceGatingPolicy
from src.engine.forecast_imputer import ForecastImputer
from src.engine.data_flow_router import DataFlowRouter
from src.engine.inference_engine import InferenceEngine


def test_gating_policy_frozen_when_missing_sources():
    policy = SourceGatingPolicy(linguist_throttle_cycles=5)
    app_state = MagicMock()

    # Only 1 local active source, 0 global
    src_local = MagicMock(id="s1", is_local=True, status=SourceStatus.ACTIVE)
    app_state.get_all_data_sources.return_value = [src_local]

    eval_res = policy.evaluate(app_state, cycle_count=1)
    assert eval_res.is_frozen is True
    assert eval_res.active_local == 1
    assert eval_res.active_global == 0
    assert eval_res.has_quarantine is False


def test_gating_policy_unfrozen_when_local_and_global_active():
    policy = SourceGatingPolicy(linguist_throttle_cycles=5)
    app_state = MagicMock()

    src_local = MagicMock(id="s1", is_local=True, status=SourceStatus.ACTIVE)
    src_global = MagicMock(id="s2", is_local=False, status=SourceStatus.ACTIVE)
    app_state.get_all_data_sources.return_value = [src_local, src_global]

    eval_res = policy.evaluate(app_state, cycle_count=2)
    assert eval_res.is_frozen is False
    assert eval_res.active_local == 1
    assert eval_res.active_global == 1
    assert eval_res.should_trigger_linguist is False


def test_gating_policy_immediate_linguist_trigger_on_quarantine():
    policy = SourceGatingPolicy(linguist_throttle_cycles=5)
    app_state = MagicMock()

    src_quarantine = MagicMock(id="s1", is_local=True, status=SourceStatus.QUARANTINE)
    app_state.get_all_data_sources.return_value = [src_quarantine]

    eval_res = policy.evaluate(app_state, cycle_count=1)
    assert eval_res.has_quarantine is True
    assert eval_res.should_trigger_linguist is True


def test_forecast_imputer_propagates_to_unobserved_nodes():
    imputer = ForecastImputer()
    graph_manager = MagicMock()
    graph_manager.get_ordered_node_ids.return_value = ["N1", "N2"]

    node_n1 = MagicMock()
    node_n1.state.last_value = 0.0
    node_n2 = MagicMock()
    node_n2.state.last_value = 25.0

    graph_manager.get_node.side_effect = lambda nid: node_n1 if nid == "N1" else node_n2

    snapshot = {
        "N1": {"value": 0.0},
        "N2": {"value": 25.0}
    }

    forecast = np.array([[18.5, 30.0]])
    imputer.impute(forecast, snapshot, graph_manager)

    # N1 was 0.0 (unobserved), so it receives the predicted value 18.5
    assert snapshot["N1"]["value"] == 18.5
    assert node_n1.state.last_value == 18.5

    # N2 was 25.0 (observed > 0), so it remains unchanged
    assert snapshot["N2"]["value"] == 25.0
    assert node_n2.state.last_value == 25.0


def test_data_flow_router_processes_payload():
    app_state = MagicMock()
    graph_manager = MagicMock()
    src_mock = MagicMock(id="sensor_1", latest_value=0.0, last_update=0.0)
    app_state.get_all_data_sources.return_value = [src_mock]

    router = DataFlowRouter(app_state=app_state, graph_manager=graph_manager)

    emitted_data = []
    router.data_processed.connect(lambda p: emitted_data.append(p))

    # Test numeric dict payload
    router.handle_data_flow("sensor_1", {"value": 42.5})

    assert src_mock.latest_value == 42.5
    graph_manager.update_node_memory.assert_called_once_with("sensor_1", 42.5, raw_payload={"value": 42.5})
    assert len(emitted_data) == 1
    assert emitted_data[0]["id"] == "sensor_1"
    assert emitted_data[0]["raw"] == 42.5


def test_inference_engine_pure_orchestrator_flow():
    app_state = MagicMock()
    graph_manager = MagicMock()
    snapshot_builder = MagicMock()
    processor = MagicMock()
    gating_policy = MagicMock()
    forecast_imputer = MagicMock()
    ingestion = MagicMock()

    # Configure active gating
    gating_eval = MagicMock(is_frozen=False, should_trigger_linguist=False)
    gating_policy.evaluate.return_value = gating_eval

    # Configure snapshot & processor
    snapshot_builder.gather_snapshot.return_value = {"N1": {"value": 10.0}}
    processor.run_logic.return_value = ({"forecast": [12.0], "alert_event": None}, None)

    engine = InferenceEngine(
        app_state=app_state,
        graph_manager=graph_manager,
        snapshot_builder=snapshot_builder,
        processor=processor,
        gating_policy=gating_policy,
        forecast_imputer=forecast_imputer,
        ingestion=ingestion
    )

    emitted_results = []
    engine.global_cycle_results.connect(lambda r: emitted_results.append(r))

    engine.run_global_cycle()

    # Verify orchestration sequence
    ingestion.check_global_fetch.assert_called_once()
    gating_policy.evaluate.assert_called_once()
    snapshot_builder.gather_snapshot.assert_called_once()
    processor.run_logic.assert_called_once_with({"N1": {"value": 10.0}})
    forecast_imputer.impute.assert_called_once()
    assert len(emitted_results) == 1
    assert "sensor_snapshot" in emitted_results[0]


def test_inference_engine_dynamic_telemetry_and_qualities():
    """Verifies that InferenceEngine computes dynamic sensor qualities and propagates live MLOps metrics."""
    app_state = MagicMock()
    graph_manager = MagicMock()
    snapshot_builder = MagicMock()
    processor = MagicMock()
    gating_policy = MagicMock()
    forecast_imputer = MagicMock()
    ingestion = MagicMock()

    # Active gating
    gating_policy.evaluate.return_value = MagicMock(is_frozen=False, should_trigger_linguist=False)
    snapshot_builder.gather_snapshot.return_value = {"N1": {"value": 10.0}, "N2": {"value": 12.0}}

    # MLOps output from Fuser via Processor
    processor.run_logic.return_value = ({
        "forecast": [10.0, 12.0],
        "fuser_loss": 0.015,
        "fuser_drift": 0.025,
        "alert_event": None
    }, None)

    # Topology and node states
    node_n1 = MagicMock()
    node_n1.state.last_loss = 0.005
    node_n1.state.last_psi = 0.010
    node_n2 = MagicMock()
    node_n2.state.last_loss = 0.007
    node_n2.state.last_psi = 0.014

    graph_manager.nodes = {"N1": node_n1, "N2": node_n2}

    # Data sources: 1 local camera on edge_1 (N1 -> N2), 1 global Waze speed, 1 global Waze flow
    src_cam = MagicMock(id="src_cam", is_local=True, semantic_type="Vehicle Count", latest_value=1.0)
    src_waze_spd = MagicMock(id="waze_spd", is_local=False, semantic_type="Vehicle Speed", latest_value=2.416) # ~8.7 km/h
    src_waze_flw = MagicMock(id="waze_flw", is_local=False, semantic_type="Traffic Flow", latest_value=1.0)

    app_state.get_all_data_sources.return_value = [src_cam, src_waze_spd, src_waze_flw]
    app_state.get_elements_for_source.side_effect = lambda sid: ["edge_1"] if sid == "src_cam" else []

    target_edge = MagicMock(id="edge_1", from_node="N1", to_node="N2", lanes=1, length=100.0, max_speed=13.89)
    app_state.get_edge.side_effect = lambda eid: target_edge if eid == "edge_1" else None

    engine = InferenceEngine(
        app_state=app_state,
        graph_manager=graph_manager,
        snapshot_builder=snapshot_builder,
        processor=processor,
        gating_policy=gating_policy,
        forecast_imputer=forecast_imputer,
        ingestion=ingestion
    )

    emitted_results = []
    engine.global_cycle_results.connect(lambda r: emitted_results.append(r))

    engine.run_global_cycle()

    assert len(emitted_results) == 1
    res = emitted_results[0]

    # Verify MLOps telemetry
    assert res["fuser_loss"] == 0.015
    assert res["fuser_drift"] == 0.025
    assert res["loss"] == 0.015
    assert res["drift"] == 0.025

    # Verify local sensor dynamic loss and quality from connected nodes (0.005 + 0.007) / 2 = 0.006
    assert abs(res["losses"]["src_cam"] - 0.006) < 1e-4
    assert abs(res["drift_scores"]["src_cam"] - 0.012) < 1e-4
    assert 90 <= res["qualities"]["src_cam"] <= 95

    # Verify global sensors dynamic loss and quality
    assert res["losses"]["waze_spd"] > 0.002
    assert res["qualities"]["waze_spd"] > 50
    assert res["losses"]["waze_flw"] > 0.002
    assert res["qualities"]["waze_flw"] > 50
