# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
import re
import gzip
import logging
from dataclasses import dataclass
from typing import List, Optional, Any, Dict, Tuple

logger = logging.getLogger("Synapse.Services.GeoProjectionService")


@dataclass
class SumoLocationParams:
    """
    Strongly-typed representation of SUMO map projection metadata.
    Enables 100% in-memory configuration without disk I/O in unit tests.
    """
    net_offset: Tuple[float, float]
    conv_boundary: Tuple[float, float, float, float]
    orig_boundary: Tuple[float, float, float, float]
    proj_parameter: str = ""

    @classmethod
    def from_dict(cls, attrs: Dict[str, str]) -> 'SumoLocationParams':
        net_offset = (0.0, 0.0)
        if "netOffset" in attrs:
            try:
                parts = [float(v) for v in attrs["netOffset"].split(",")]
                net_offset = (parts[0], parts[1])
            except Exception:
                pass

        conv_boundary = (0.0, 0.0, 0.0, 0.0)
        if "convBoundary" in attrs:
            try:
                parts = [float(v) for v in attrs["convBoundary"].split(",")]
                conv_boundary = (parts[0], parts[1], parts[2], parts[3])
            except Exception:
                pass

        orig_boundary = (0.0, 0.0, 0.0, 0.0)
        if "origBoundary" in attrs:
            try:
                parts = [float(v) for v in attrs["origBoundary"].split(",")]
                orig_boundary = (parts[0], parts[1], parts[2], parts[3])
            except Exception:
                pass

        proj_parameter = attrs.get("projParameter", "")
        return cls(
            net_offset=net_offset,
            conv_boundary=conv_boundary,
            orig_boundary=orig_boundary,
            proj_parameter=proj_parameter
        )


class GeoProjectionService:
    """
    Domain & Infrastructure Service responsible for geodetic projection
    between WGS84 GPS (longitude, latitude) and SUMO local coordinates (x, y) in meters.

    SOLID Compliance:
    - [SRP] Only handles coordinate conversion and projection metadata.
    - [DIP] Can be initialized directly with in-memory SumoLocationParams (decoupled from filesystem).
    """

    def __init__(self, params: Optional[SumoLocationParams] = None):
        self.params = params
        self._pyproj_instance = None
        self._init_proj()

    def _init_proj(self):
        if self.params and self.params.proj_parameter and self.params.proj_parameter != "!":
            try:
                import pyproj
                self._pyproj_instance = pyproj.Proj(self.params.proj_parameter)
            except Exception as e:
                logger.debug(f"[GeoProjectionService] Pyproj unavailable or failed ({e}). Fallback to linear boundary.")
                self._pyproj_instance = None

    def project_point(self, lon: float, lat: float) -> Tuple[float, float]:
        """Projects a single (lon, lat) point to SUMO (x, y)."""
        if not self.params:
            return lon, lat

        # Check bounds if orig_boundary is defined
        ob = self.params.orig_boundary
        if ob != (0.0, 0.0, 0.0, 0.0):
            min_lon, min_lat, max_lon, max_lat = ob
            # 0.5 degrees tolerance around city bbox
            if not ((min_lon - 0.5) <= lon <= (max_lon + 0.5) and (min_lat - 0.5) <= lat <= (max_lat + 0.5)):
                return lon, lat

        # 1. Pyproj method
        if self._pyproj_instance is not None:
            try:
                ux, uy = self._pyproj_instance(lon, lat)
                ox, oy = self.params.net_offset
                return ux + ox, uy + oy
            except Exception as e:
                logger.debug(f"[GeoProjectionService] pyproj point projection failed: {e}")

        # 2. Linear boundary interpolation fallback
        cb = self.params.conv_boundary
        if ob != (0.0, 0.0, 0.0, 0.0) and cb != (0.0, 0.0, 0.0, 0.0):
            min_lon, min_lat, max_lon, max_lat = ob
            c_min_x, c_min_y, c_max_x, c_max_y = cb
            rx = (lon - min_lon) / (max_lon - min_lon) if max_lon != min_lon else 0.5
            ry = (lat - min_lat) / (max_lat - min_lat) if max_lat != min_lat else 0.5
            sx = c_min_x + rx * (c_max_x - c_min_x)
            sy = c_min_y + ry * (c_max_y - c_min_y)
            return sx, sy

        return lon, lat

    def project(self, polyline: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Projects a polyline of (lon, lat) tuples to SUMO (x, y)."""
        if not polyline:
            return []
        return [self.project_point(p[0], p[1]) for p in polyline]


# Cache for map files on disk
_FILE_SERVICE_CACHE: Dict[str, GeoProjectionService] = {}


def get_projection_service_for_map(map_file_path: Optional[str]) -> GeoProjectionService:
    """
    Factory function: retrieves or constructs a GeoProjectionService from a map file.
    Caches parsed metadata in memory.
    """
    if not map_file_path:
        return GeoProjectionService()

    clean_path = str(map_file_path).strip().strip('"\'')
    if clean_path in _FILE_SERVICE_CACHE:
        return _FILE_SERVICE_CACHE[clean_path]

    if not os.path.exists(clean_path):
        return GeoProjectionService()

    try:
        is_gz = clean_path.endswith(".gz")
        open_fn = gzip.open if is_gz else open
        with open_fn(clean_path, "rb") as f:
            chunk = f.read(8192).decode("utf-8", errors="ignore")
            m = re.search(r"<location\s+([^>]+)/>", chunk)
            if m:
                attrs = dict(re.findall(r"(\w+)=\"([^\"]*)\"", m.group(1)))
                params = SumoLocationParams.from_dict(attrs)
                svc = GeoProjectionService(params=params)
                _FILE_SERVICE_CACHE[clean_path] = svc
                return svc
    except Exception as e:
        logger.debug(f"[GeoProjectionService] Erro ao extrair <location> de {clean_path}: {e}")

    return GeoProjectionService()


def project_polyline_to_sumo(
    polyline: List[Tuple[float, float]],
    map_file_path: Optional[str] = None,
) -> List[Tuple[float, float]]:
    """Functional shortcut for project_polyline_to_sumo."""
    svc = get_projection_service_for_map(map_file_path)
    return svc.project(polyline)
