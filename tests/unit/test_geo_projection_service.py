# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import pytest
from src.services.geo_projection_service import GeoProjectionService, SumoLocationParams


@pytest.fixture
def in_memory_projection_service():
    """
    Clean Architecture / DIP Fixture:
    Provides an in-memory GeoProjectionService without any disk I/O.
    """
    params = SumoLocationParams(
        net_offset=(-475481.54, 2600660.66),
        conv_boundary=(0.00, 0.00, 715.96, 930.36),
        orig_boundary=(-51.240163, -23.515986, -51.233151, -23.507576),
        proj_parameter="+proj=utm +zone=22 +ellps=WGS84 +datum=WGS84 +units=m +no_defs"
    )
    return GeoProjectionService(params=params)


def test_geo_projection_service_in_memory(in_memory_projection_service):
    """Verifies projection from WGS84 GPS degrees to SUMO metric coordinates 100% in RAM."""
    gps_coords = [(-51.2351221, -23.5097475)]
    projected = in_memory_projection_service.project(gps_coords)
    assert len(projected) == 1
    sx, sy = projected[0]
    # In this region sx ~ 514, sy ~ 690
    assert 500.0 <= sx <= 530.0
    assert 670.0 <= sy <= 710.0
