# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import logging
from typing import List, Optional, Any, Dict, Tuple

logger = logging.getLogger("Synapse.Pipeline.GlobalPolylineExtractor")


class GlobalPolylineExtractor:
    """
    Interface Adapter pipeline component responsible for extracting geodetic
    polylines/coordinates (lon, lat) from external global sensor telemetry.

    SOLID Compliance:
    - [SRP] Exclusively responsible for unpacking third-party schemas (TomTom, Waze, etc.).
    - [OCP] Provider-specific extraction methods are separated, facilitating extension
            to new providers without affecting core logic.
    """

    def extract(
        self,
        data_chunk: Optional[List[Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[List[Tuple[float, float]]]:
        """
        Extracts road polyline or coordinates from global sensor telemetry sample or metadata.
        Strictly sample-efficient: requires only 1 sample (data_chunk[0]).
        Returns a list of (lon, lat) tuples in WGS84 GPS degrees, or None.
        """
        if data_chunk and len(data_chunk) > 0:
            sample = data_chunk[0]
            if isinstance(sample, list) and len(sample) > 0:
                sample = sample[0]
            if isinstance(sample, dict):
                # 1. TomTom format
                tomtom_poly = self._extract_tomtom(sample)
                if tomtom_poly:
                    return tomtom_poly

                # 2. Waze jams / alerts
                waze_poly = self._extract_waze(sample)
                if waze_poly:
                    return waze_poly

                # 3. Generic array coordinates (line, polyline, coordinates, etc.)
                generic_poly = self._extract_generic(sample)
                if generic_poly:
                    return generic_poly

                # 4. Single coordinate point in sample
                single_pt = self._extract_single_point(sample)
                if single_pt:
                    return single_pt

        # 5. Metadata fallback
        if metadata and isinstance(metadata, dict):
            return self._extract_from_metadata(metadata)

        return None

    def _extract_tomtom(self, sample: Dict[str, Any]) -> Optional[List[Tuple[float, float]]]:
        """Extracts coordinates from TomTom flowSegmentData."""
        flow_data = sample.get("flowSegmentData")
        if not isinstance(flow_data, dict):
            return None

        coords = flow_data.get("coordinates")
        if isinstance(coords, dict):
            coords = coords.get("coordinate")
        if not isinstance(coords, list):
            return None

        polyline: List[Tuple[float, float]] = []
        for pt in coords:
            if isinstance(pt, dict):
                lat = pt.get("latitude") if "latitude" in pt else pt.get("lat")
                lon = pt.get("longitude") if "longitude" in pt else pt.get("lon")
                if lat is not None and lon is not None:
                    try:
                        polyline.append((float(lon), float(lat)))
                    except (ValueError, TypeError):
                        pass

        return polyline if len(polyline) >= 1 else None

    def _extract_waze(self, sample: Dict[str, Any]) -> Optional[List[Tuple[float, float]]]:
        """Extracts coordinates from Waze jams or alerts."""
        jams = sample.get("jams")
        if isinstance(jams, list) and jams:
            first_jam = jams[0]
            if isinstance(first_jam, dict):
                line = first_jam.get("line")
                if isinstance(line, list):
                    polyline: List[Tuple[float, float]] = []
                    for pt in line:
                        if isinstance(pt, dict):
                            x = pt.get("x") if "x" in pt else (pt.get("lon") or pt.get("longitude"))
                            y = pt.get("y") if "y" in pt else (pt.get("lat") or pt.get("latitude"))
                            if x is not None and y is not None:
                                try:
                                    polyline.append((float(x), float(y)))
                                except (ValueError, TypeError):
                                    pass
                    if len(polyline) >= 1:
                        return polyline

        alerts = sample.get("alerts")
        if isinstance(alerts, list) and alerts:
            first_alert = alerts[0]
            if isinstance(first_alert, dict):
                loc = first_alert.get("location")
                if isinstance(loc, dict):
                    x = loc.get("x") if "x" in loc else (loc.get("lon") or loc.get("longitude"))
                    y = loc.get("y") if "y" in loc else (loc.get("lat") or loc.get("latitude"))
                    if x is not None and y is not None:
                        try:
                            return [(float(x), float(y))]
                        except (ValueError, TypeError):
                            pass

        return None

    def _extract_generic(self, sample: Dict[str, Any]) -> Optional[List[Tuple[float, float]]]:
        """Extracts from generic array fields: line, polyline, coordinates, points, shape."""
        polyline: List[Tuple[float, float]] = []
        for key in ("line", "polyline", "coordinates", "points", "shape"):
            raw_list = sample.get(key)
            if isinstance(raw_list, list) and raw_list:
                for pt in raw_list:
                    if isinstance(pt, (list, tuple)) and len(pt) >= 2:
                        try:
                            polyline.append((float(pt[0]), float(pt[1])))
                        except (ValueError, TypeError):
                            pass
                    elif isinstance(pt, dict):
                        x = pt.get("x") if "x" in pt else (pt.get("lon") or pt.get("longitude"))
                        y = pt.get("y") if "y" in pt else (pt.get("lat") or pt.get("latitude"))
                        if x is not None and y is not None:
                            try:
                                polyline.append((float(x), float(y)))
                            except (ValueError, TypeError):
                                pass
                if len(polyline) >= 1:
                    return polyline
        return None

    def _extract_single_point(self, sample: Dict[str, Any]) -> Optional[List[Tuple[float, float]]]:
        """Extracts a single coordinate point from sample root."""
        x = sample.get("lon") or sample.get("longitude") or sample.get("x")
        y = sample.get("lat") or sample.get("latitude") or sample.get("y")
        if x is not None and y is not None:
            try:
                return [(float(x), float(y))]
            except (ValueError, TypeError):
                pass
        return None

    def _extract_from_metadata(self, metadata: Dict[str, Any]) -> Optional[List[Tuple[float, float]]]:
        """Fallback extraction from DataSource metadata dictionary."""
        poly_meta = metadata.get("polyline") or metadata.get("coordinates")
        if isinstance(poly_meta, list) and poly_meta:
            polyline: List[Tuple[float, float]] = []
            for pt in poly_meta:
                if isinstance(pt, (list, tuple)) and len(pt) >= 2:
                    try:
                        polyline.append((float(pt[0]), float(pt[1])))
                    except (ValueError, TypeError):
                        pass
                elif isinstance(pt, dict):
                    x = pt.get("x") if "x" in pt else (pt.get("lon") or pt.get("longitude"))
                    y = pt.get("y") if "y" in pt else (pt.get("lat") or pt.get("latitude"))
                    if x is not None and y is not None:
                        try:
                            polyline.append((float(x), float(y)))
                        except (ValueError, TypeError):
                            pass
            if len(polyline) >= 1:
                return polyline

        pos_x = metadata.get("x") or metadata.get("lon") or metadata.get("longitude")
        pos_y = metadata.get("y") or metadata.get("lat") or metadata.get("latitude")
        if pos_x is not None and pos_y is not None:
            try:
                return [(float(pos_x), float(pos_y))]
            except (ValueError, TypeError):
                pass

        return None


# Module-level convenience function
_DEFAULT_EXTRACTOR = GlobalPolylineExtractor()


def extract_global_polyline(
    data_chunk: Optional[List[Any]],
    metadata: Optional[Dict[str, Any]] = None,
) -> Optional[List[Tuple[float, float]]]:
    """Convenience functional interface for GlobalPolylineExtractor."""
    return _DEFAULT_EXTRACTOR.extract(data_chunk, metadata)
