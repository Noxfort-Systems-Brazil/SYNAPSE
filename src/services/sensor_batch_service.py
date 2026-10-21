# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import csv
import io
from typing import Any, Dict, List, Optional, Tuple

from src.domain.entities import DataSource, SourceStatus, SourceType
from src.infrastructure.network_service import NetworkService
from src.utils.logging_setup import get_logger

logger = get_logger("SensorBatchService")


class SensorBatchService:
    """
    Handles bulk ingestion, topology pre-flight validation, and configuration export
    for local sensors in SYNAPSE (SOLID: SRP & DIP).
    """

    @staticmethod
    def parse_csv_records(csv_content: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Parses raw CSV content expecting 'name' and 'location' headers.
        Tolerates comma or semicolon delimiters and case-insensitive headers.
        """
        records: List[Dict[str, Any]] = []
        errors: List[str] = []

        if not csv_content or not csv_content.strip():
            return [], ["O arquivo CSV fornecido está vazio."]

        lines = [line.strip() for line in csv_content.strip().splitlines() if line.strip()]
        if not lines:
            return [], ["O arquivo CSV não possui linhas válidas."]

        # Detect delimiter (comma vs semicolon)
        header_sample = lines[0]
        delimiter = ';' if ';' in header_sample and ',' not in header_sample else ','

        try:
            reader = csv.reader(io.StringIO("\n".join(lines)), delimiter=delimiter)
            header = next(reader, None)
            if not header:
                return [], ["Não foi possível identificar o cabeçalho do CSV."]

            # Map column indices for 'name' and 'location'
            name_idx = -1
            location_idx = -1

            for idx, col in enumerate(header):
                clean_col = col.strip().lower()
                if clean_col in ("name", "nome"):
                    name_idx = idx
                elif clean_col in ("location", "localizacao", "localização", "element_id", "element"):
                    location_idx = idx

            if name_idx == -1 or location_idx == -1:
                return [], [
                    f"Cabeçalho inválido. É obrigatório conter as colunas 'name' e 'location'. "
                    f"Colunas encontradas: {', '.join(header)}"
                ]

            for row_num, row in enumerate(reader, start=2):
                if not row or not any(field.strip() for field in row):
                    continue

                if len(row) <= max(name_idx, location_idx):
                    errors.append(f"Linha {row_num}: Quantidade insuficiente de colunas.")
                    continue

                sensor_name = row[name_idx].strip()
                location_val = row[location_idx].strip()

                if not sensor_name:
                    errors.append(f"Linha {row_num}: O campo 'name' não pode ser vazio.")
                    continue
                if not location_val:
                    errors.append(f"Linha {row_num}: O campo 'location' não pode ser vazio.")
                    continue

                records.append({
                    "line": row_num,
                    "name": sensor_name,
                    "location": location_val,
                })

        except Exception as ex:
            logger.error(f"Failed to parse CSV content: {ex}", exc_info=True)
            return [], [f"Falha ao processar formatação do CSV: {str(ex)}"]

        return records, errors

    @classmethod
    def preview_manifest(cls, csv_content: str, topology: Any) -> Dict[str, Any]:
        """
        Dry-run pre-flight validation of the manifest against loaded topology.
        Checks if each location resolves to a MapNode or MapEdge without mutating state.
        """
        records, parse_errors = cls.parse_csv_records(csv_content)

        items: List[Dict[str, Any]] = []
        valid_count = 0
        error_count = len(parse_errors)

        for rec in records:
            line_no = rec["line"]
            name = rec["name"]
            location = rec["location"]

            resolved_type = "INVALID"
            error_msg: Optional[str] = None

            # Resolve against topology
            has_node = False
            has_edge = False

            if topology:
                get_node_fn = getattr(topology, "get_node", None)
                get_edge_fn = getattr(topology, "get_edge", None)
                if callable(get_node_fn) and get_node_fn(location):
                    has_node = True
                if callable(get_edge_fn) and get_edge_fn(location):
                    has_edge = True

            if has_node:
                resolved_type = "NODE"
                valid_count += 1
            elif has_edge:
                resolved_type = "EDGE"
                valid_count += 1
            else:
                # If no map is loaded or location not found
                get_nodes_fn = getattr(topology, "get_all_nodes", None) if topology else None
                if callable(get_nodes_fn) and len(get_nodes_fn()) > 0:
                    error_msg = f"Localização '{location}' não foi encontrada nos nós ou arestas da malha SUMO."
                else:
                    # In case no map is currently loaded
                    error_msg = f"Aviso: Mapa viário não carregado. Localização '{location}' pendente de validação."
                    resolved_type = "UNKNOWN"
                    valid_count += 1

                if resolved_type == "INVALID":
                    error_count += 1

            items.append({
                "line": line_no,
                "name": name,
                "location": location,
                "resolved_type": resolved_type,
                "error": error_msg,
            })

        return {
            "total": len(items) + len(parse_errors),
            "valid_count": valid_count,
            "error_count": error_count,
            "parse_errors": parse_errors,
            "items": items,
        }

    @classmethod
    def import_manifest(
        cls,
        csv_content: str,
        app_state: Any,
        host: Optional[str] = None,
        port: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Executes atomic batch creation and association of local sensors from CSV manifest.
        Generates camera connection profiles with dedicated push endpoints.
        """
        topology = getattr(app_state, "topology", None)
        preview = cls.preview_manifest(csv_content, topology)

        if preview["valid_count"] == 0:
            return {
                "success": False,
                "message": "Nenhum sensor válido encontrado para importação.",
                "imported_count": 0,
                "items": [],
                "errors": preview["parse_errors"],
            }

        # Resolve network target for push URLs
        net_info = NetworkService.get_network_info()
        target_host = host or net_info.get("local_ip", "127.0.0.1")
        target_port = port or net_info.get("gateway_port", 8081)
        base_endpoint = net_info.get("unified_endpoint") if not (host or port) else f"http://{target_host}:{target_port}"

        imported_items: List[Dict[str, Any]] = []
        sources_mgr = getattr(app_state, "sources", None)

        for item in preview["items"]:
            if item["resolved_type"] == "INVALID":
                continue

            name = item["name"]
            location = item["location"]
            resolved_type = item["resolved_type"]

            # Monotonic next source ID from app_state
            next_id_fn = getattr(app_state, "get_next_source_id", None) or getattr(
                sources_mgr, "get_next_source_id", None
            )
            src_id = next_id_fn() if callable(next_id_fn) else f"src_{len(imported_items) + 1}"

            push_url = f"{base_endpoint}/{src_id}"

            # 1. Create DataSource in QUARANTINE
            src = DataSource(
                id=src_id,
                name=name,
                is_local=True,
                source_type=SourceType.API,
                connection_string=push_url,
                status=SourceStatus.QUARANTINE,
                metadata={
                    "resolved_type": resolved_type,
                    "target_element": location,
                    "batch_imported": True,
                },
            )

            # 2. Add to application state
            add_fn = getattr(app_state, "add_data_source", None) or getattr(sources_mgr, "add", None)
            if callable(add_fn):
                add_fn(src)

            # 3. Associate with map element
            if sources_mgr is not None:
                sources_mgr.associate(src_id, location)
            sig = getattr(app_state, "data_association_changed", None)
            if sig is not None:
                sig.emit(src_id, location)

            imported_items.append({
                "id": src_id,
                "name": name,
                "location": location,
                "resolved_type": resolved_type,
                "push_url": push_url,
            })

        # Save to storage in bulk if available
        save_fn = getattr(sources_mgr, "save", None) or getattr(sources_mgr, "_save_to_storage", None)
        if callable(save_fn):
            try:
                save_fn()
            except Exception as ex:
                logger.warning(f"Could not trigger batch storage save: {ex}")

        logger.info(f"✅ Batch Ingestion Complete: {len(imported_items)} local sensors provisioned.")

        return {
            "success": True,
            "imported_count": len(imported_items),
            "items": imported_items,
        }
