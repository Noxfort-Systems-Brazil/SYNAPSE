# SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
# Copyright (C) 2026 Noxfort Systems
#
# File: tests/unit/test_sensor_batch_service.py

import pytest
from unittest.mock import MagicMock
from src.services.sensor_batch_service import SensorBatchService
from src.domain.entities import MapNode, MapEdge, SourceStatus


def test_parse_csv_records_comma_and_semicolon():
    # Comma test
    csv_comma = "name,location\nCam 01 - Paulista,cluster_12048\nRadar Tunel,-edge_4401"
    records, errors = SensorBatchService.parse_csv_records(csv_comma)
    assert len(errors) == 0
    assert len(records) == 2
    assert records[0]["name"] == "Cam 01 - Paulista"
    assert records[0]["location"] == "cluster_12048"
    assert records[1]["name"] == "Radar Tunel"
    assert records[1]["location"] == "-edge_4401"

    # Semicolon test
    csv_semi = "name;location\nCam 02;cluster_99\n"
    records_semi, errors_semi = SensorBatchService.parse_csv_records(csv_semi)
    assert len(errors_semi) == 0
    assert len(records_semi) == 1
    assert records_semi[0]["name"] == "Cam 02"
    assert records_semi[0]["location"] == "cluster_99"


def test_parse_csv_records_invalid_headers():
    csv_bad = "device,coord\nCam 01,123"
    records, errors = SensorBatchService.parse_csv_records(csv_bad)
    assert len(records) == 0
    assert len(errors) == 1
    assert "name" in errors[0] and "location" in errors[0]


def test_preview_manifest_topology_resolution():
    mock_topology = MagicMock()
    mock_topology.get_all_nodes.return_value = ["cluster_10"]
    mock_topology.get_node.side_effect = lambda nid: MapNode(id=nid, x=0, y=0, node_type="priority") if nid == "cluster_10" else None
    mock_topology.get_edge.side_effect = lambda eid: MapEdge(id=eid, from_node="a", to_node="b", shape=[]) if eid == "edge_50" else None

    csv_content = """name,location
Camera Cruzamento,cluster_10
Radar Rua,edge_50
Sensor Inexistente,cluster_unknown
"""
    preview = SensorBatchService.preview_manifest(csv_content, mock_topology)
    assert preview["total"] == 3
    assert preview["valid_count"] == 2
    assert preview["error_count"] == 1

    items = preview["items"]
    assert items[0]["resolved_type"] == "NODE"
    assert items[0]["error"] is None
    assert items[1]["resolved_type"] == "EDGE"
    assert items[1]["error"] is None
    assert items[2]["resolved_type"] == "INVALID"
    assert items[2]["error"] is not None


def test_import_manifest_creation_and_export():
    mock_topology = MagicMock()
    mock_topology.get_all_nodes.return_value = ["cluster_10"]
    mock_topology.get_node.side_effect = lambda nid: MapNode(id=nid, x=0, y=0, node_type="priority") if nid == "cluster_10" else None
    mock_topology.get_edge.return_value = None

    mock_sources = MagicMock()
    curr_id = [1]
    def next_id():
        val = f"src_{curr_id[0]}"
        curr_id[0] += 1
        return val
    mock_sources.get_next_source_id.side_effect = next_id

    mock_app_state = MagicMock()
    mock_app_state.topology = mock_topology
    mock_app_state.sources = mock_sources
    mock_app_state.get_next_source_id.side_effect = next_id

    added_sources = []
    mock_app_state.add_data_source.side_effect = lambda s: added_sources.append(s)

    csv_content = """name,location
Camera 01,cluster_10
Camera 02,cluster_10
"""
    result = SensorBatchService.import_manifest(
        csv_content, mock_app_state, host="10.0.0.99", port=8080
    )

    assert result["success"] is True
    assert result["imported_count"] == 2
    assert len(added_sources) == 2

    s1 = added_sources[0]
    assert s1.id == "src_1"
    assert s1.name == "Camera 01"
    assert s1.is_local is True
    assert s1.status == SourceStatus.QUARANTINE
    assert s1.connection_string == "http://10.0.0.99:8080/src_1"

    mock_sources.associate.assert_any_call("src_1", "cluster_10")
    mock_sources.associate.assert_any_call("src_2", "cluster_10")

    export_items = result["items"]
    assert export_items[0]["push_url"] == "http://10.0.0.99:8080/src_1"
    assert export_items[1]["push_url"] == "http://10.0.0.99:8080/src_2"


def test_source_command_handler_batch():
    from src.handlers.source_handler import SourceCommandHandler
    from src.ipc.ipc_protocol import IpcMessage

    mock_app_state = MagicMock()
    mock_app_state.topology = None
    mock_app_state.get_next_source_id.return_value = "src_1"

    handler = SourceCommandHandler(app_state=mock_app_state)

    # Preview
    preview_msg = IpcMessage(
        action="preview_batch_sources",
        payload={"csv_content": "name,location\nCam 01,loc_1"}
    )
    res_prev = handler.handle_preview_batch_sources(preview_msg)
    assert res_prev["total"] == 1
    assert res_prev["items"][0]["name"] == "Cam 01"

    # Import
    import_msg = IpcMessage(
        action="import_batch_sources",
        payload={"csv_content": "name,location\nCam 01,loc_1", "host": "127.0.0.1", "port": 8081}
    )
    res_imp = handler.handle_import_batch_sources(import_msg)
    assert res_imp["success"] is True
    assert res_imp["imported_count"] == 1

