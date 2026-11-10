# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import pytest
from unittest.mock import MagicMock
from src.services.sensor_batch_service import SensorBatchService
from src.domain.entities import MapNode, MapEdge, SourceStatus


def test_parse_csv_records_comma_and_semicolon():
    # Comma test
    csv_comma = """name,type,id,address
Cam 01 - Paulista,local,cluster_12048,192.168.1.50
Radar Tunel,local,-edge_4401,
Waze Traffic Feed,global,,https://api.waze.com/traffic
"""
    records, errors = SensorBatchService.parse_csv_records(csv_comma)
    assert len(errors) == 0
    assert len(records) == 3

    assert records[0]["name"] == "Cam 01 - Paulista"
    assert records[0]["type"] == "local"
    assert records[0]["id"] == "cluster_12048"
    assert records[0]["address"] == "192.168.1.50"

    assert records[1]["name"] == "Radar Tunel"
    assert records[1]["type"] == "local"
    assert records[1]["id"] == "-edge_4401"
    assert records[1]["address"] == ""

    assert records[2]["name"] == "Waze Traffic Feed"
    assert records[2]["type"] == "global"
    assert records[2]["id"] == ""
    assert records[2]["address"] == "https://api.waze.com/traffic"

    # Semicolon test
    csv_semi = "name;type;id;address\nCam 02;local;cluster_99;10.0.0.1\nFeed TomTom;global;;https://api.tomtom.com/flow\n"
    records_semi, errors_semi = SensorBatchService.parse_csv_records(csv_semi)
    assert len(errors_semi) == 0
    assert len(records_semi) == 2
    assert records_semi[0]["name"] == "Cam 02"
    assert records_semi[0]["type"] == "local"
    assert records_semi[0]["id"] == "cluster_99"
    assert records_semi[1]["name"] == "Feed TomTom"
    assert records_semi[1]["type"] == "global"
    assert records_semi[1]["address"] == "https://api.tomtom.com/flow"


def test_parse_csv_records_invalid_headers():
    csv_bad = "device,coord\nCam 01,123"
    records, errors = SensorBatchService.parse_csv_records(csv_bad)
    assert len(records) == 0
    assert len(errors) == 1
    assert "name,type,id,address" in errors[0]


def test_parse_csv_records_validation_rules():
    # Local missing id (SUMO address)
    csv_missing_id = "name,type,id,address\nCam 01,local,,192.168.1.1"
    records, errors = SensorBatchService.parse_csv_records(csv_missing_id)
    assert len(records) == 0
    assert len(errors) == 1
    assert "endereço na malha SUMO" in errors[0]

    # Global missing address (URL/IP)
    csv_missing_addr = "name,type,id,address\nWaze Feed,global,cluster_10,"
    records, errors = SensorBatchService.parse_csv_records(csv_missing_addr)
    assert len(records) == 0
    assert len(errors) == 1
    assert "address" in errors[0]

    # Invalid type
    csv_invalid_type = "name,type,id,address\nSensor X,satellite,node_1,1.1.1.1"
    records, errors = SensorBatchService.parse_csv_records(csv_invalid_type)
    assert len(records) == 0
    assert len(errors) == 1
    assert "Tipo inválido" in errors[0]


def test_preview_manifest_topology_resolution():
    mock_topology = MagicMock()
    mock_topology.get_all_nodes.return_value = ["cluster_10"]
    mock_topology.get_node.side_effect = lambda nid: MapNode(id=nid, x=0, y=0, node_type="priority") if nid == "cluster_10" else None
    mock_topology.get_edge.side_effect = lambda eid: MapEdge(id=eid, from_node="a", to_node="b", shape=[]) if eid == "edge_50" else None

    csv_content = """name,type,id,address
Camera Cruzamento,local,cluster_10,192.168.1.10
Radar Rua,local,edge_50,
Sensor Inexistente,local,cluster_unknown,
Waze Feed Externo,global,,https://api.waze.com/sp
"""
    preview = SensorBatchService.preview_manifest(csv_content, mock_topology)
    assert preview["total"] == 4
    assert preview["valid_count"] == 3
    assert preview["error_count"] == 1

    items = preview["items"]
    # Item 0: Local Node
    assert items[0]["name"] == "Camera Cruzamento"
    assert items[0]["type"] == "local"
    assert items[0]["resolved_type"] == "NODE"
    assert items[0]["error"] is None

    # Item 1: Local Edge
    assert items[1]["name"] == "Radar Rua"
    assert items[1]["type"] == "local"
    assert items[1]["resolved_type"] == "EDGE"
    assert items[1]["error"] is None

    # Item 2: Local Invalid
    assert items[2]["name"] == "Sensor Inexistente"
    assert items[2]["type"] == "local"
    assert items[2]["resolved_type"] == "INVALID"
    assert items[2]["error"] is not None

    # Item 3: Global API
    assert items[3]["name"] == "Waze Feed Externo"
    assert items[3]["type"] == "global"
    assert items[3]["resolved_type"] == "GLOBAL_API"
    assert items[3]["error"] is None


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

    csv_content = """name,type,id,address
Camera 01,local,cluster_10,192.168.1.100
Global Traffic API,global,,https://api.external.com/feed
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
    assert s1.metadata.get("camera_ip") == "192.168.1.100"
    mock_sources.associate.assert_called_once_with("src_1", "cluster_10")

    s2 = added_sources[1]
    assert s2.id == "src_2"
    assert s2.name == "Global Traffic API"
    assert s2.is_local is False
    assert s2.status == SourceStatus.QUARANTINE
    assert s2.connection_string == "https://api.external.com/feed"

    export_items = result["items"]
    assert export_items[0]["type"] == "local"
    assert export_items[0]["push_url"] == "http://10.0.0.99:8080/src_1"
    assert export_items[1]["type"] == "global"
    assert export_items[1]["push_url"] == "https://api.external.com/feed"


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
        payload={"csv_content": "name,type,id,address\nCam 01,local,loc_1,192.168.0.10"}
    )
    res_prev = handler.handle_preview_batch_sources(preview_msg)
    assert res_prev["total"] == 1
    assert res_prev["items"][0]["name"] == "Cam 01"
    assert res_prev["items"][0]["type"] == "local"

    # Import
    import_msg = IpcMessage(
        action="import_batch_sources",
        payload={
            "csv_content": "name,type,id,address\nCam 01,local,loc_1,192.168.0.10",
            "host": "127.0.0.1",
            "port": 8081
        }
    )
    res_imp = handler.handle_import_batch_sources(import_msg)
    assert res_imp["success"] is True
    assert res_imp["imported_count"] == 1

