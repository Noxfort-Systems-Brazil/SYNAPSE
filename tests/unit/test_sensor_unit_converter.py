# SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
# Copyright (C) 2026 Noxfort Systems
#
# File: tests/unit/test_sensor_unit_converter.py

import pytest
from unittest.mock import MagicMock
from src.physics.sensor_unit_converter import SensorUnitConverter
from src.domain.entities import DataSource, SourceType, SourceStatus
from src.engine.data_flow_router import DataFlowRouter


def test_converter_canonical_rules():
    # Rule 1: km/h -> m/s (72 km/h == 20 m/s)
    assert pytest.approx(SensorUnitConverter.convert(72.0, 1), rel=1e-4) == 20.0

    # Rule 2: mph -> m/s (100 mph == 44.704 m/s)
    assert pytest.approx(SensorUnitConverter.convert(100.0, 2), rel=1e-4) == 44.704

    # Rule 3: veh/h -> veh/s (3600 veh/h == 1.0 veh/s)
    assert pytest.approx(SensorUnitConverter.convert(3600.0, 3), rel=1e-4) == 1.0

    # Rule 4: veh/min -> veh/s (120 veh/min == 2.0 veh/s)
    assert pytest.approx(SensorUnitConverter.convert(120.0, 4), rel=1e-4) == 2.0

    # Rule 5: Direct SI / Identity
    assert pytest.approx(SensorUnitConverter.convert(15.75, 5), rel=1e-4) == 15.75

    # Unmapped rule returns None to enforce discard and avoid hallucination
    assert SensorUnitConverter.convert(99.0, 999) is None
    assert SensorUnitConverter.convert(99.0, None) is None


def test_rule_for_unit_mapping():
    assert SensorUnitConverter.rule_for_unit("km/h") == 1
    assert SensorUnitConverter.rule_for_unit("KMH") == 1
    assert SensorUnitConverter.rule_for_unit("mph") == 2
    assert SensorUnitConverter.rule_for_unit("veh/h") == 3
    assert SensorUnitConverter.rule_for_unit("vph") == 3
    assert SensorUnitConverter.rule_for_unit("veic/h") == 3
    assert SensorUnitConverter.rule_for_unit("veh/min") == 4
    assert SensorUnitConverter.rule_for_unit("vpm") == 4
    assert SensorUnitConverter.rule_for_unit("m/s") == 5
    assert SensorUnitConverter.rule_for_unit("veh/s") == 5
    assert SensorUnitConverter.rule_for_unit("vehicles") == 5
    assert SensorUnitConverter.rule_for_unit("count") == 5

    # Out of scope / unconvertible units MUST return None
    assert SensorUnitConverter.rule_for_unit("unknown") is None
    assert SensorUnitConverter.rule_for_unit("celsius") is None
    assert SensorUnitConverter.rule_for_unit("psi") is None
    assert SensorUnitConverter.rule_for_unit("units") is None
    assert SensorUnitConverter.rule_for_unit(None) is None
    assert SensorUnitConverter.rule_for_unit("") is None

    assert SensorUnitConverter.is_supported_unit("km/h") is True
    assert SensorUnitConverter.is_supported_unit("celsius") is False


def test_data_flow_router_dynamic_extraction_and_conversion():
    # Setup mock AppState
    mock_app_state = MagicMock()
    mock_graph_manager = MagicMock()

    # Dynamic sensor with metadata: km/h speed
    source_speed = DataSource(
        id="src_radar_dynamic",
        name="Dynamic Radar",
        source_type=SourceType.API,
        status=SourceStatus.ACTIVE,
        metadata={
            "extraction_path": ["telemetry", "speed_kmh"],
            "conversion_rule": 1  # km/h -> m/s
        }
    )

    # Dynamic sensor with metadata: flow in veh/h
    source_flow = DataSource(
        id="src_loop_dynamic",
        name="Dynamic Loop",
        source_type=SourceType.API,
        status=SourceStatus.ACTIVE,
        metadata={
            "extraction_path": ["flowSegmentData", "currentFlow"],
            "conversion_rule": 3  # veh/h -> veh/s
        }
    )

    # Sensor with an unconvertible / invalid rule (to be discarded)
    source_invalid = DataSource(
        id="src_temperature_sensor",
        name="Weather Station",
        source_type=SourceType.API,
        status=SourceStatus.ACTIVE,
        metadata={
            "extraction_path": ["temp"],
            "conversion_rule": None  # Unconvertible unit
        }
    )

    # Rejected sensor
    source_rejected = DataSource(
        id="src_rejected_sensor",
        name="Rejected Loop",
        source_type=SourceType.API,
        status=SourceStatus.REJECTED,
        metadata={
            "conversion_rule": 1
        }
    )

    sources_map = {
        "src_radar_dynamic": source_speed,
        "src_loop_dynamic": source_flow,
        "src_temperature_sensor": source_invalid,
        "src_rejected_sensor": source_rejected
    }
    mock_app_state.get_data_source.side_effect = lambda sid: sources_map.get(sid)
    mock_app_state.get_all_data_sources.return_value = list(sources_map.values())

    router = DataFlowRouter(
        app_state=mock_app_state,
        graph_manager=mock_graph_manager
    )

    emitted_signals = []
    router.data_processed.connect(lambda data: emitted_signals.append(data))

    # 1. Process Speed Radar (72 km/h -> 20 m/s)
    router.handle_data_flow(
        "src_radar_dynamic",
        {"telemetry": {"speed_kmh": 72.0}}
    )

    assert pytest.approx(source_speed.latest_value, rel=1e-4) == 20.0
    mock_graph_manager.update_node_memory.assert_called_with(
        "src_radar_dynamic", 20.0, raw_payload={"telemetry": {"speed_kmh": 72.0}}
    )
    assert len(emitted_signals) == 1
    assert emitted_signals[0]["raw"] == 72.0
    assert pytest.approx(emitted_signals[0]["value"], rel=1e-4) == 20.0

    # 2. Process Flow Loop (1800 veh/h -> 0.5 veh/s)
    router.handle_data_flow(
        "src_loop_dynamic",
        {"flowSegmentData": {"currentFlow": 1800.0}}
    )

    assert pytest.approx(source_flow.latest_value, rel=1e-4) == 0.5
    mock_graph_manager.update_node_memory.assert_called_with(
        "src_loop_dynamic", 0.5, raw_payload={"flowSegmentData": {"currentFlow": 1800.0}}
    )
    assert len(emitted_signals) == 2

    # 3. Discard unconvertible temperature sensor (anti-hallucination)
    mock_graph_manager.reset_mock()
    router.handle_data_flow(
        "src_temperature_sensor",
        {"temp": 28.5}
    )
    # MUST BE DISCARDED: no memory update, no emitted signal
    mock_graph_manager.update_node_memory.assert_not_called()
    assert len(emitted_signals) == 2

    # 4. Discard rejected sensor
    router.handle_data_flow(
        "src_rejected_sensor",
        {"speed": 50.0}
    )
    mock_graph_manager.update_node_memory.assert_not_called()
    assert len(emitted_signals) == 2


def test_linguist_rejects_unconvertible_unit():
    """Verifies that LinguistService rejects sensors with unconvertible physical units (preventing hallucinations)."""
    from src.services.linguist_service import LinguistService

    app_state = MagicMock()
    ingestion = MagicMock()
    agent_factory = MagicMock()
    classifier = MagicMock()
    validator = MagicMock()

    service = LinguistService(
        app_state=app_state,
        ingestion_worker=ingestion,
        agent_factory=agent_factory,
        semantic_classifier=classifier,
        physics_validator=validator
    )

    source = DataSource(id="temp_01", name="Thermometer", status=SourceStatus.QUARANTINE)
    pipeline = MagicMock()
    pipeline.has_enough_data.return_value = True
    pipeline.get_quarantine_data.return_value = [{"temp": 30.0}] * 5

    # Classified as Temperature in Celsius (unsupported / outside traffic SI)
    classifier.classify.return_value = ("Temperature", "Celsius", 0.9)
    validator.validate.return_value = True

    linguist = MagicMock()
    linguist.train_step.return_value = 0.001
    agent_factory.get_or_create_linguist.return_value = linguist

    service._process_quarantine_source(source, pipeline)

    # Must be REJECTED!
    assert source.status == SourceStatus.REJECTED

