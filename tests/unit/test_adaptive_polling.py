# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from unittest.mock import MagicMock, patch
import pytest

from src.adapters.adaptive_poller import AdaptivePollingController
from src.adapters.go_push_adapter import GoPushAdapter
from src.domain.entities import DataSource, SourceStatus


def test_adaptive_poller_initialization_and_bounds():
    controller = AdaptivePollingController(
        min_interval_s=60.0,
        max_interval_s=300.0,
        step_up_s=30.0,
    )
    
    # Active source starts at min_interval (60s)
    interval = controller.register_source("tomtom_corridor")
    assert interval == 60.0
    assert controller.get_interval("tomtom_corridor") == 60.0
    
    # Quarantine source starts at quarantine_interval (10s)
    q_interval = controller.register_source("waze_broken", is_quarantine=True)
    assert q_interval == 10.0
    assert controller.get_interval("waze_broken") == 10.0


def test_adaptive_poller_steps_up_on_identical_payload():
    """Identical payloads indicate the external API has not refreshed yet; step up to save quota."""
    controller = AdaptivePollingController(
        min_interval_s=60.0,
        max_interval_s=300.0,
        step_up_s=30.0,
    )
    controller.register_source("src_stable")
    
    payload = {"speed": 50.0, "status": "ok"}
    
    # First packet: baseline established, interval remains 60s
    interval, changed = controller.evaluate_packet("src_stable", payload)
    assert interval == 60.0
    assert changed is False
    
    # 2nd packet (identical payload): steps up to 90s
    interval, changed = controller.evaluate_packet("src_stable", payload)
    assert interval == 90.0
    assert changed is True
    
    # 3rd packet (identical payload): steps up to 120s
    interval, changed = controller.evaluate_packet("src_stable", payload)
    assert interval == 120.0
    assert changed is True
    
    # Repeat until max ceiling (300s)
    for _ in range(10):
        interval, _ = controller.evaluate_packet("src_stable", payload)
        
    assert interval == 300.0
    assert controller.get_interval("src_stable") == 300.0


def test_adaptive_poller_contracts_immediately_on_high_volatility():
    """When a severe traffic shift (|Δv| >= 15%) is detected, interval collapses immediately to 60s."""
    controller = AdaptivePollingController(
        min_interval_s=60.0,
        max_interval_s=300.0,
        step_up_s=30.0,
        volatility_threshold=0.15,
    )
    controller.register_source("highway_segment", initial_interval=300.0)
    assert controller.get_interval("highway_segment") == 300.0
    
    # Baseline at 80 km/h
    controller.evaluate_packet("highway_segment", {"speed": 80.0})
    
    # Sudden drop to 40 km/h (|80 - 40| / 80 = 50% >= 15%)
    interval, changed = controller.evaluate_packet("highway_segment", {"speed": 40.0})
    assert interval == 60.0
    assert changed is True
    
    # Traffic remains volatile (jump from 40 to 65 -> 62.5% change)
    interval, changed = controller.evaluate_packet("highway_segment", {"speed": 65.0})
    assert interval == 60.0
    assert changed is False  # already at 60.0s


def test_adaptive_poller_supports_nested_tomtom_and_waze_formats():
    """Tests payload parsing for TomTom flowSegmentData and alternative key schemas."""
    controller = AdaptivePollingController()
    controller.register_source("tomtom_live")
    
    tomtom_payload_1 = {
        "flowSegmentData": {
            "currentSpeed": 60.0,
            "freeFlowSpeed": 65.0,
            "currentTravelTime": 120,
        }
    }
    
    controller.evaluate_packet("tomtom_live", tomtom_payload_1)
    state = controller.get_state("tomtom_live")
    assert state.last_metric_value == 60.0
    
    # Sudden congestion: currentSpeed falls to 25.0
    tomtom_payload_2 = {
        "flowSegmentData": {
            "currentSpeed": 25.0,
            "freeFlowSpeed": 65.0,
            "currentTravelTime": 290,
        }
    }
    interval, changed = controller.evaluate_packet("tomtom_live", tomtom_payload_2)
    assert interval == 60.0


def test_adaptive_poller_quarantine_mode():
    """In quarantine mode, interval remains pinned to quarantine_interval_s (10.0s)."""
    controller = AdaptivePollingController(quarantine_interval_s=10.0)
    controller.register_source("erratic_sensor", is_quarantine=True)
    
    interval, changed = controller.evaluate_packet(
        "erratic_sensor",
        {"speed": 50.0},
        is_quarantine=True,
    )
    assert interval == 10.0
    assert changed is False


def test_go_push_adapter_adaptive_polling_integration():
    """Verifies that GoPushAdapter dynamically calls transport.register_poll_source when interval changes."""
    adapter = GoPushAdapter()
    
    with patch.object(adapter.transport, "register_poll_source") as mock_reg, \
         patch.object(adapter.transport, "unregister_poll_source") as mock_unreg:
        
        # 1. Register global active source
        src = DataSource(
            id="global_tomtom",
            name="TomTom Flow",
            is_local=False,
            connection_string="https://api.tomtom.com/traffic/flow",
            status=SourceStatus.ACTIVE,
        )
        adapter.register_source(src)
        
        # Initially registered with 60.0s
        mock_reg.assert_called_once_with(
            "global_tomtom",
            "https://api.tomtom.com/traffic/flow",
            interval_sec=60.0,
        )
        mock_reg.reset_mock()
        
        # 2. Ingest first packet (sets baseline)
        payload = {"speed": 70.0}
        adapter._on_transport_packet("global_tomtom", payload, metadata={})
        mock_reg.assert_not_called()  # No interval change yet
        
        # 3. Ingest identical packet (provider cache detected -> step up to 90s)
        adapter._on_transport_packet("global_tomtom", payload, metadata={})
        mock_reg.assert_called_once_with(
            "global_tomtom",
            "https://api.tomtom.com/traffic/flow",
            interval_sec=90.0,
        )
        mock_reg.reset_mock()
        
        # 4. Ingest abrupt speed drop (70.0 -> 30.0 -> snap back to 60s)
        adapter._on_transport_packet("global_tomtom", {"speed": 30.0}, metadata={})
        mock_reg.assert_called_once_with(
            "global_tomtom",
            "https://api.tomtom.com/traffic/flow",
            interval_sec=60.0,
        )
        
        # 5. Unregister cleans up
        adapter.unregister_source("global_tomtom")
        mock_unreg.assert_called_once_with("global_tomtom")
        assert adapter.adaptive_controller.get_state("global_tomtom") is None
