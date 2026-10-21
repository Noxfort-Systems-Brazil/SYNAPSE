# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import pytest
from src.pipeline.global_polyline_extractor import GlobalPolylineExtractor


def test_extract_global_polyline_tomtom():
    """Verifies that 1 single sample from TomTom payload extracts WGS84 coordinates."""
    extractor = GlobalPolylineExtractor()
    tomtom_chunk = [
        {
            "flowSegmentData": {
                "currentSpeed_kmh": 48.0,
                "coordinates": {
                    "coordinate": [
                        {"latitude": -23.5097475, "longitude": -51.2351221},
                        {"latitude": -23.5098522, "longitude": -51.2352354}
                    ]
                }
            }
        }
    ]
    polyline = extractor.extract(tomtom_chunk)
    assert polyline is not None
    assert len(polyline) == 2
    assert polyline[0] == (-51.2351221, -23.5097475)


def test_extract_global_polyline_waze():
    """Verifies that 1 single sample from Waze payload extracts WGS84 coordinates."""
    extractor = GlobalPolylineExtractor()
    waze_chunk = [
        {
            "jams": [
                {
                    "line": [
                        {"x": -51.236102, "y": -23.512398},
                        {"x": -51.236315, "y": -23.512521}
                    ]
                }
            ]
        }
    ]
    polyline = extractor.extract(waze_chunk)
    assert polyline is not None
    assert len(polyline) == 2
    assert polyline[0] == (-51.236102, -23.512398)


def test_extract_global_polyline_list_wrapper():
    """
    Verifies that a list-wrapped payload sample (e.g. from TomTom / REST feed)
    is properly unwrapped and coordinates are extracted.
    """
    extractor = GlobalPolylineExtractor()
    tomtom_list_chunk = [
        [
            {
                "flowSegmentData": {
                    "segmentId": "-103342059#0",
                    "coordinates": [
                        {"latitude": -23.5135, "longitude": -51.2351},
                        {"latitude": -23.5138, "longitude": -51.2354}
                    ]
                }
            }
        ]
    ]
    coords = extractor.extract(tomtom_list_chunk)
    assert coords is not None
    assert len(coords) == 2
    assert coords[0] == (-51.2351, -23.5135)
    assert coords[1] == (-51.2354, -23.5138)
