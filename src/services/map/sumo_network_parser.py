# SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
# Copyright (C) 2026 Noxfort Systems
#
# File: src/services/map/sumo_network_parser.py
# Description: Pure SUMO Network XML/GZIP parser extracting topological ground truth (SOLID: SRP).

import gzip
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass

from src.domain.entities import MapNode, MapEdge
from src.logging.facade import get_logger

logger = get_logger("SumoNetworkParser")


@dataclass
class ParsedNetwork:
    nodes: List[MapNode]
    edges: List[MapEdge]
    node_lookup: Dict[str, MapNode]


class SumoNetworkParser:
    """Parses SUMO network files (.net.xml and .net.xml.gz) into domain entities."""

    @staticmethod
    def _clean_tag(elem: ET.Element) -> str:
        return elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag

    @classmethod
    def _open_xml_tree(cls, path: Path) -> ET.ElementTree:
        is_gzip = False
        try:
            with open(path, 'rb') as f_check:
                header = f_check.read(2)
                if header == b'\x1f\x8b':
                    is_gzip = True
        except Exception as e:
            logger.warning(f"Não foi possível inspecionar cabeçalho do arquivo: {e}")
            is_gzip = str(path).lower().endswith('.gz')

        if is_gzip or str(path).lower().endswith('.gz'):
            try:
                with gzip.open(path, 'rb') as source:
                    return ET.parse(source)
            except Exception as gz_err:
                logger.warning(f"Falha ao abrir como GZIP ({gz_err}). Tentando parser XML direto...")
                try:
                    return ET.parse(str(path))
                except Exception as xml_err:
                    raise RuntimeError(f"Falha ao processar arquivo GZIP/XML: {gz_err} / {xml_err}") from gz_err
        else:
            try:
                return ET.parse(str(path))
            except Exception as xml_err:
                logger.warning(f"Falha ao ler como XML puro ({xml_err}). Tentando como GZIP...")
                try:
                    with gzip.open(path, 'rb') as source:
                        return ET.parse(source)
                except Exception:
                    raise xml_err

    @classmethod
    def parse(cls, path: Path) -> ParsedNetwork:
        tree = cls._open_xml_tree(path)
        root = tree.getroot()
        if root is None:
            raise ValueError(f"Estrutura XML vazia no arquivo SUMO: {path.name}")

        nodes: List[MapNode] = []
        edges: List[MapEdge] = []
        node_lookup: Dict[str, MapNode] = {}

        # ── 1. Parse Junctions (Nodes) ──
        junction_elements = [elem for elem in root.iter() if cls._clean_tag(elem) == 'junction']
        for junction in junction_elements:
            j_type = junction.get('type', '')
            if j_type == 'internal':
                continue

            j_id = junction.get('id')
            if not j_id or j_id.startswith(':'):
                continue

            x_val: Optional[float] = None
            y_val: Optional[float] = None

            x_attr = junction.get('x')
            y_attr = junction.get('y')
            if x_attr is not None and y_attr is not None:
                try:
                    x_val = float(x_attr)
                    y_val = float(y_attr)
                except (ValueError, TypeError):
                    pass

            # Fallback to shape coordinates if x/y missing
            if x_val is None or y_val is None:
                shape = junction.get('shape')
                if shape:
                    try:
                        first_pt = shape.strip().split()[0].split(',')
                        x_val = float(first_pt[0])
                        y_val = float(first_pt[1])
                    except (ValueError, TypeError, IndexError):
                        pass

            if x_val is None or y_val is None:
                continue

            tl_id = junction.get('tl') or junction.get('tlLogic')
            if not tl_id and str(j_type).startswith('traffic_light'):
                tl_id = j_id

            j_name = junction.get('name')
            if not j_name:
                for child in junction:
                    if cls._clean_tag(child) == 'param' and child.get('key') in ('name', 'junction_name', 'osm_name'):
                        j_name = child.get('value')
                        break
            j_name = j_name.strip() if j_name and str(j_name).strip() else None

            node = MapNode(id=j_id, x=x_val, y=y_val, node_type=str(j_type), tl_logic_id=tl_id, real_name=j_name)
            nodes.append(node)
            node_lookup[j_id] = node

        if not nodes:
            raise ValueError(f"Nenhum nó viário físico válido encontrado no mapa SUMO: {path.name}")

        # ── 2. Parse Streets (Edges) ──
        edge_elements = [elem for elem in root.iter() if cls._clean_tag(elem) == 'edge']
        for edge in edge_elements:
            func = edge.get('function', '')
            if func in ('internal', 'crossing', 'walkingarea'):
                continue

            e_id = edge.get('id')
            if not e_id or e_id.startswith(':'):
                continue

            from_id = edge.get('from')
            to_id = edge.get('to')

            if from_id in node_lookup and to_id in node_lookup:
                lanes = [child for child in edge if cls._clean_tag(child) == 'lane']

                # Geometry (Shape)
                shape_points: List[Tuple[float, float]] = []
                shape_str = lanes[0].get('shape') if lanes else None
                if not shape_str:
                    shape_str = edge.get('shape')

                if shape_str:
                    try:
                        for point_str in shape_str.strip().split():
                            coords = point_str.split(',')
                            if len(coords) >= 2:
                                shape_points.append((float(coords[0]), float(coords[1])))
                    except (ValueError, IndexError):
                        shape_points = []

                if not shape_points:
                    fn = node_lookup[from_id]
                    tn = node_lookup[to_id]
                    shape_points = [(fn.x, fn.y), (tn.x, tn.y)]

                # Length
                try:
                    length = float(edge.get('length', 0.0))
                    if length <= 0.0 and lanes:
                        length = float(lanes[0].get('length', 1.0))
                    if length <= 0.0:
                        fn = node_lookup[from_id]
                        tn = node_lookup[to_id]
                        length = max(1.0, float(((fn.x - tn.x) ** 2 + (fn.y - tn.y) ** 2) ** 0.5))
                except (ValueError, TypeError):
                    length = 1.0

                # Max Speed
                try:
                    max_speed = float(edge.get('speed', 13.89))
                    if lanes and 'speed' in lanes[0].attrib:
                        max_speed = float(lanes[0].get('speed', max_speed))
                except (ValueError, TypeError):
                    max_speed = 13.89

                num_lanes = max(1, len(lanes)) if lanes else 1

                # Street Name
                street_name = edge.get('name')
                if not street_name:
                    for child in edge:
                        if cls._clean_tag(child) == 'param' and child.get('key') in ('name', 'street_name', 'osm_name'):
                            street_name = child.get('value')
                            break
                # Edge Type and Priority
                edge_type = edge.get('type', 'highway.residential') or 'highway.residential'
                try:
                    priority = int(edge.get('priority', 1))
                except (ValueError, TypeError):
                    priority = 1

                map_edge = MapEdge(
                    id=e_id,
                    from_node=from_id,
                    to_node=to_id,
                    shape=shape_points,
                    max_speed=max_speed,
                    lanes=num_lanes,
                    length=length,
                    real_name=street_name,
                    edge_type=str(edge_type),
                    priority=priority
                )
                edges.append(map_edge)

        return ParsedNetwork(nodes=nodes, edges=edges, node_lookup=node_lookup)
