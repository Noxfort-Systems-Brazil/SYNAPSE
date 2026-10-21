# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Linguist & PINN Neural Subsystem Test Suite Aggregator (SOLID & Clean Architecture).
Delegates tests across modular suites under tests/unit/linguist/:
- test_neuro_symbolic_model.py: Neural forward, PINN residuals, knowledge transfer.
- test_series_and_classifier.py: Extraction pipeline, semantic classifier, specialist inference.
- test_sensor_physical_validator.py: Kinematics, dynamic road topology limits, speed limits.
"""

from unittest.mock import MagicMock
from src.services.linguist_service import LinguistService
from src.domain.app_state import AppState
from src.domain.entities import DataSource, SourceType, SourceStatus

from tests.unit.linguist.test_neuro_symbolic_model import (
    test_neuro_symbolic_pinn_residuals,
    test_linguist_agent_train_and_inference_pinn,
    test_modality_conditioned_physics_loss,
    test_knowledge_transfer_service_with_warmup,
)
from tests.unit.linguist.test_series_and_classifier import (
    test_series_extractor_camera_detections_and_timestamps,
    test_series_extractor_tomtom_nested,
    test_semantic_classifier_camera_and_tomtom,
    test_specialist_agent_autonomous_raw_packet_inference,
)
from tests.unit.linguist.test_sensor_physical_validator import (
    test_sensor_physical_validator_modality,
    test_sensor_physical_validator_dynamic_topology,
    test_sensor_physical_validator_dynamic_speed_limit,
    test_sensor_physical_validator_dynamic_delta_time_counts,
    test_sensor_physical_validator_offpeak_empty_street,
    test_sensor_physical_validator_kinematic_acceleration_rejection,
)


def test_linguist_service_promotes_camera_with_detections():
    """Verifies that LinguistService successfully promotes camera payload with detections and teaches TCN."""
    app_state = MagicMock(spec=AppState)
    ingestion = MagicMock()
    pipeline = MagicMock()
    ingestion.get_pipeline.return_value = pipeline
    agent_factory = MagicMock()

    src = DataSource(
        id="src_cam_1",
        name="Camera Av Paulista",
        source_type=SourceType.API,
        is_local=True,
        status=SourceStatus.QUARANTINE,
    )
    app_state.get_all_data_sources.return_value = [src]

    pipeline.has_enough_data.return_value = True
    pipeline.get_quarantine_data.return_value = [
        {"packet_id": "101", "sensor_id": "cam_01", "detections": [{"id": 1}, {"id": 2}]},
        {"packet_id": "102", "sensor_id": "cam_01", "detections": [{"id": 1}, {"id": 2}, {"id": 3}]},
        {"packet_id": "103", "sensor_id": "cam_01", "detections": [{"id": 1}]},
        {"packet_id": "104", "sensor_id": "cam_01", "detections": [{"id": 1}, {"id": 2}]},
        {"packet_id": "105", "sensor_id": "cam_01", "detections": [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}]},
    ]

    mock_linguist = MagicMock()
    mock_linguist.train_step.return_value = 0.02
    mock_linguist.inference.return_value = {"is_valid": True, "is_anomaly": False, "physics_residual": 0.01}
    agent_factory.get_or_create_linguist.return_value = mock_linguist

    mock_specialist = MagicMock()
    agent_factory.get_or_create_specialist.return_value = mock_specialist

    service = LinguistService(app_state, ingestion, agent_factory)
    service.spatial_reconciler = MagicMock()
    service.spatial_reconciler.find_candidate_edges.return_value = [MagicMock(id="edge_1")]
    service.spatial_reconciler.reconcile_orientation.return_value = ({"target_edge_id": "edge_1"}, None)
    service.run_check()

    assert src.status == SourceStatus.ACTIVE
    assert src.semantic_type == "Vehicle Count"
    assert src.inferred_unit == "vehicles"
    pipeline.promote_to_active.assert_called_once_with("src_cam_1")
    agent_factory.release_linguist.assert_called_once_with("src_cam_1")


def test_linguist_service_promotes_tomtom_feed():
    """Verifies that LinguistService promotes nested TomTom speed feed and releases linguist."""
    app_state = MagicMock(spec=AppState)
    ingestion = MagicMock()
    pipeline = MagicMock()
    ingestion.get_pipeline.return_value = pipeline
    agent_factory = MagicMock()

    src = DataSource(
        id="src_tomtom_1",
        name="Tom Tom",
        source_type=SourceType.API,
        is_local=False,
        status=SourceStatus.QUARANTINE,
    )
    app_state.get_all_data_sources.return_value = [src]

    pipeline.has_enough_data.return_value = True
    pipeline.get_quarantine_data.return_value = [
        {"flowSegmentData": {"segmentId": "seg_1", "currentSpeed": 45.0}},
        {"flowSegmentData": {"segmentId": "seg_1", "currentSpeed": 46.0}},
        {"flowSegmentData": {"segmentId": "seg_1", "currentSpeed": 44.0}},
        {"flowSegmentData": {"segmentId": "seg_1", "currentSpeed": 48.0}},
        {"flowSegmentData": {"segmentId": "seg_1", "currentSpeed": 45.0}},
    ]

    mock_linguist = MagicMock()
    mock_linguist.train_step.return_value = 0.02
    mock_linguist.inference.return_value = {"is_valid": True, "is_anomaly": False, "physics_residual": 0.01}
    agent_factory.get_or_create_linguist.return_value = mock_linguist
    agent_factory.get_or_create_specialist.return_value = MagicMock()

    service = LinguistService(app_state, ingestion, agent_factory)
    service.spatial_reconciler = MagicMock()
    service.spatial_reconciler.find_candidate_edges.return_value = [MagicMock(id="edge_1")]
    service.spatial_reconciler.reconcile_orientation.return_value = ({"target_edge_id": "edge_1"}, None)
    service.run_check()

    assert src.status == SourceStatus.ACTIVE
    assert src.semantic_type == "Vehicle Speed"
    assert src.inferred_unit == "km/h"
    pipeline.promote_to_active.assert_called_once_with("src_tomtom_1")
    agent_factory.release_linguist.assert_called_once_with("src_tomtom_1")
