# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import pytest
import numpy as np

from src.pipeline.series_extractor_pipeline import SeriesExtractorPipeline
from src.services.semantic_classifier import SemanticClassifier
from src.agents.specialist_agent import SpecialistAgent
from src.domain.entities import DataSource, SourceType


def test_series_extractor_camera_detections_and_timestamps():
    """Verifies that SeriesExtractorPipeline extracts vehicle detection counts and ignores IDs/timestamps."""
    extractor = SeriesExtractorPipeline()

    camera_payloads = [
        {
            "packet_id": "100825",
            "sensor_id": "cam_01",
            "timestamp": 1787196563800,
            "detections": [
                {"track_id": 1, "class": "car"},
                {"track_id": 2, "class": "bus"},
                {"track_id": 3, "class": "car"}
            ]
        },
        {
            "packet_id": "100827",
            "sensor_id": "cam_01",
            "timestamp": 1787196564800,
            "detections": [
                {"track_id": 1, "class": "car"}
            ]
        }
    ]

    arr = extractor.extract(camera_payloads)
    assert len(arr) == 2
    assert arr[0] == pytest.approx(3.0)
    assert arr[1] == pytest.approx(1.0)


def test_series_extractor_tomtom_nested():
    """Verifies that SeriesExtractorPipeline extracts currentSpeed from nested flowSegmentData."""
    extractor = SeriesExtractorPipeline()

    tomtom_payload = [{
        "flowSegmentData": {
            "segmentId": "seg_01",
            "currentSpeed": 48.5,
            "freeFlowSpeed": 60.0,
            "currentTravelTime": 120
        }
    }]

    arr = extractor.extract(tomtom_payload)
    assert len(arr) == 1
    assert arr[0] == pytest.approx(48.5)


def test_semantic_classifier_camera_and_tomtom():
    """Verifies that SemanticClassifier identifies Camera as Vehicle Count and TomTom as Vehicle Speed."""
    classifier = SemanticClassifier()

    cam_src = DataSource(id="src_camera_1", name="Camera", source_type=SourceType.API, is_local=True)
    cam_chunk = [{"packet_id": "100", "detections": [{"track_id": 1}]}]
    sem_type, unit, conf = classifier.classify(cam_src, np.array([1.0]), cam_chunk)
    assert sem_type == "Vehicle Count"
    assert unit == "vehicles"
    assert conf >= 0.9

    tomtom_src = DataSource(id="src_tom_tom_1", name="Tom Tom", source_type=SourceType.API, is_local=False)
    tomtom_chunk = [{"flowSegmentData": {"currentSpeed": 50.0}}]
    sem_type, unit, conf = classifier.classify(tomtom_src, np.array([50.0]), tomtom_chunk)
    assert sem_type == "Vehicle Speed"
    assert unit == "km/h"


def test_specialist_agent_autonomous_raw_packet_inference():
    """Verifies that SpecialistAgent with attached extractor processes raw sensor packets autonomously."""
    specialist = SpecialistAgent()
    extractor = SeriesExtractorPipeline()

    specialist.set_extractor(extractor, semantic_type="Vehicle Count", unit="vehicles")

    raw_packets = [
        {"packet_id": "100", "detections": [{"id": 1}, {"id": 2}]},
        {"packet_id": "101", "detections": [{"id": 1}, {"id": 2}, {"id": 3}]},
        {"packet_id": "102", "detections": [{"id": 1}]},
        {"packet_id": "103", "detections": [{"id": 1}, {"id": 2}]},
        {"packet_id": "104", "detections": [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}]}
    ]

    embedding = specialist.inference(raw_packets)

    assert isinstance(embedding, np.ndarray)
    assert len(embedding) == 32
    assert specialist.semantic_type == "Vehicle Count"
    assert specialist.inferred_unit == "vehicles"


def test_series_extractor_recipe_compilation_and_si_conversion():
    """Verifies that compile_recipe builds an O(1) nested path and converts km/h to m/s."""
    extractor = SeriesExtractorPipeline()
    tomtom_samples = [
        {"flowSegmentData": {"currentSpeed": 72.0}},
        {"flowSegmentData": {"currentSpeed": 54.0}},
        {"flowSegmentData": {"currentSpeed": 36.0}},
        {"flowSegmentData": {"currentSpeed": 90.0}},
        {"flowSegmentData": {"currentSpeed": 108.0}},
    ]

    recipe = extractor.compile_recipe(tomtom_samples, modality="Vehicle Speed", unit="km/h", to_si=True)

    assert recipe["mode"] == "nested_key"
    assert recipe["field_path"] == ["flowSegmentData", "currentSpeed"]
    assert recipe["si_unit"] == "m/s"
    assert recipe["si_factor"] == pytest.approx(1.0 / 3.6)

    arr = extractor.extract(tomtom_samples)
    assert len(arr) == 5
    assert arr[0] == pytest.approx(20.0)   # 72 / 3.6 = 20.0 m/s
    assert arr[1] == pytest.approx(15.0)   # 54 / 3.6 = 15.0 m/s
    assert arr[2] == pytest.approx(10.0)   # 36 / 3.6 = 10.0 m/s
    assert arr[3] == pytest.approx(25.0)   # 90 / 3.6 = 25.0 m/s
    assert arr[4] == pytest.approx(30.0)   # 108 / 3.6 = 30.0 m/s


def test_series_extractor_flow_si_conversion():
    """Verifies that compile_recipe converts veh/h flow measurements to SI veh/s."""
    extractor = SeriesExtractorPipeline()
    loop_samples = [
        {"sensor_id": "loop_1", "flow": 1800.0},
        {"sensor_id": "loop_1", "flow": 3600.0},
        {"sensor_id": "loop_1", "flow": 900.0},
        {"sensor_id": "loop_1", "flow": 720.0},
        {"sensor_id": "loop_1", "flow": 0.0},
    ]

    recipe = extractor.compile_recipe(loop_samples, modality="Vehicle Flow", unit="veh/h", to_si=True)

    assert recipe["mode"] == "direct_key"
    assert recipe["field_path"] == ["flow"]
    assert recipe["si_unit"] == "veh/s"
    assert recipe["si_factor"] == pytest.approx(1.0 / 3600.0)

    arr = extractor.extract(loop_samples)
    assert len(arr) == 5
    assert arr[0] == pytest.approx(0.5)    # 1800 / 3600 = 0.5 veh/s
    assert arr[1] == pytest.approx(1.0)    # 3600 / 3600 = 1.0 veh/s
    assert arr[2] == pytest.approx(0.25)   # 900 / 3600 = 0.25 veh/s


def test_series_extractor_csv_loop_telemetry():
    """Verifies that SeriesExtractorPipeline parses CSV loop passage rows."""
    extractor = SeriesExtractorPipeline()
    csv_samples = [
        ["2026-10-18,14:53:35,loop_01,-23.512239,-51.235280,1,CAR,56,404"],
        ["2026-10-18,14:53:36,loop_01,-23.512239,-51.235280,1,SUV,48,472"],
        ["2026-10-18,14:53:37,loop_01,-23.512239,-51.235280,1,BUS,52,955"],
    ]

    # Test count extraction
    recipe = extractor.compile_recipe(csv_samples, modality="Vehicle Count", unit="vehicles", to_si=True)
    assert recipe["mode"] == "csv_row"
    arr = extractor.extract(csv_samples)
    assert len(arr) == 3
    assert arr[0] == 1.0
    assert arr[1] == 1.0
    assert arr[2] == 1.0

    # Test speed extraction
    extractor_speed = SeriesExtractorPipeline()
    recipe_spd = extractor_speed.compile_recipe(csv_samples, modality="Vehicle Speed", unit="km/h", to_si=True)
    arr_spd = extractor_speed.extract(csv_samples)
    assert len(arr_spd) == 3
    assert arr_spd[0] == pytest.approx(56.0 / 3.6)
    assert arr_spd[1] == pytest.approx(48.0 / 3.6)
    assert arr_spd[2] == pytest.approx(52.0 / 3.6)


