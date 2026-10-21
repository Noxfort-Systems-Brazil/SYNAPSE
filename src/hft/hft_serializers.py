# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
import time
import sys
from typing import Dict, Any

# Ensure proto modules are reachable
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

from proto import synapse_hft_pb2


class HFTSerializer:
    """
    Responsible solely for converting Python Dictionaries into gRPC Protobuf Messages.
    """

    @staticmethod
    def pack_scenario(data: Dict[str, Any]) -> synapse_hft_pb2.ScenarioDefinition:
        """
        Converts a map definition dict into a Protobuf ScenarioDefinition.
        Handles both file-based binary read and logical graph parsing.
        """
        scenario = synapse_hft_pb2.ScenarioDefinition()
        scenario.map_hash = data.get("map_hash", "v1.0")

        # 1. Binary Upload (Raw Map File)
        file_path = data.get("map_file_path")
        if file_path and os.path.exists(file_path):
            try:
                file_name = os.path.basename(file_path)
                scenario.map_file_name = file_name

                with open(file_path, "rb") as f:
                    file_bytes = f.read()
                    scenario.map_file_content = file_bytes
            except Exception as e:
                print(f"[HFT-Serializer] Warning: File Read Error ({file_path}): {e}")

        # 1.5 JSON Peak Schedule Transfer (Offline Context)
        peak_schedule = data.get("peak_schedule_json")
        if peak_schedule:
            scenario.peak_schedule_json = peak_schedule

        # 2. Logical Topology (Nodes & Edges)
        if "graph" in data:
            for n_data in data["graph"].get("nodes", []):
                node = scenario.graph.nodes.add()
                node.id = str(n_data.get("id"))
                node.type = str(n_data.get("type", "priority"))
                node.x = float(n_data.get("x", 0.0))
                node.y = float(n_data.get("y", 0.0))

                tl_id = n_data.get("tl_logic_id")
                if tl_id:
                    node.tl_logic_id = str(tl_id)

            for e_data in data["graph"].get("edges", []):
                edge = scenario.graph.edges.add()
                edge.id = str(e_data.get("id"))
                edge.source_node = str(e_data.get("source_node"))
                edge.target_node = str(e_data.get("target_node"))
                edge.length = float(e_data.get("length", 100.0))
                edge.lanes = int(e_data.get("lanes", 1))
                edge.max_speed = float(e_data.get("limit", 13.89))
                edge.signal_group_id = int(e_data.get("signal_group_id", -1))

        # 3. Geometric Shapes (Polygons/Lanes)
        if "geometry" in data:
            shapes_data = data["geometry"].get("shapes", [])
            for s_data in shapes_data:
                shape = scenario.geometry.shapes.add()
                shape.edge_id = str(s_data.get("edge_id"))
                shape.coords.extend(s_data.get("coords", []))

        return scenario

    @staticmethod
    def pack_traffic_frame(data: Dict[str, Any]) -> synapse_hft_pb2.TrafficFrame:
        """
        Converts a realtime traffic snapshot into a Protobuf TrafficFrame.
        """
        frame = synapse_hft_pb2.TrafficFrame()
        frame.timestamp = float(data.get("timestamp", time.time()))
        frame.sequence_id = int(time.time() * 1000)

        traffic_list = data.get("traffic", [])
        edges_dict = data.get("edges", {})

        if traffic_list:
            for entry in traffic_list:
                edge_id = str(entry.get("edge_id", ""))
                if not edge_id:
                    continue

                state = synapse_hft_pb2.EdgeState()
                state.occupancy = float(entry.get("occupancy", 0.0))
                state.mean_speed = float(entry.get("speed", 0.0))
                state.queue_length = int(entry.get("queue", 0))
                state.density = float(entry.get("density", 0.0))

                frame.edges[edge_id].CopyFrom(state)

        elif edges_dict:
            for edge_id, metrics in edges_dict.items():
                state = synapse_hft_pb2.EdgeState()
                state.occupancy = float(metrics.get("occupancy", 0.0))
                state.mean_speed = float(metrics.get("speed", 0.0))
                state.queue_length = int(metrics.get("queue", 0))
                state.density = float(metrics.get("density", 0.0))

                frame.edges[edge_id].CopyFrom(state)

        return frame
