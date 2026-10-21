# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from unittest.mock import MagicMock, patch
import pytest

from src.adapters.go_push_adapter import GoPushAdapter
from src.go.binary_manager import GoBinaryManager
from src.go.pipe_dispatcher import GoPipeDispatcher
from src.go.pipe_process import GoPipeProcess
from src.go.subprocess_transport import GoSubprocessTransport
from src.interfaces.gateway_transport import IGatewayTransport


def test_binary_manager_resolution_and_validation():
    mgr = GoBinaryManager()
    assert mgr.bin_path.endswith("bin/synapse-gateway")

    with patch("os.path.isfile", return_value=True), \
         patch("os.access", return_value=True):
        assert mgr.ensure_ready() is True

    with patch("os.path.isfile", return_value=False), \
         patch.object(mgr, "compile_binary", return_value=True) as mock_compile:
        assert mgr.ensure_ready() is True
        mock_compile.assert_called_once()


def test_pipe_process_lifecycle():
    proc = GoPipeProcess(bin_path="/tmp/mock-bin")
    assert proc.is_running is False

    with patch("subprocess.Popen") as mock_popen:
        mock_instance = MagicMock()
        mock_instance.poll.return_value = None
        mock_instance.pid = 9999
        mock_popen.return_value = mock_instance

        assert proc.spawn() is True
        assert proc.is_running is True
        assert proc.pid == 9999

        # Test line write
        assert proc.write_line('{"cmd":"PING"}') is True
        mock_instance.stdin.write.assert_called_with('{"cmd":"PING"}\n')

        # Test terminate
        proc.terminate_gracefully(timeout=0.1)
        mock_instance.wait.assert_called_once()


def test_pipe_dispatcher_ocp_extensibility():
    """
    Asserts Open/Closed Principle: new events can be handled without modifying dispatcher core.
    """
    dispatcher = GoPipeDispatcher()
    custom_events = []

    # Plug a brand new event dynamically (OCP)
    dispatcher.register_handler("CUSTOM_SENSOR_EVENT", lambda msg: custom_events.append(msg))

    simulated_stdout = [
        '{"event":"CUSTOM_SENSOR_EVENT","alert":"ROAD_ICE_DETECTED"}\n',
        '{"event":"PONG"}\n',
    ]

    dispatcher._stdout_loop(simulated_stdout)

    assert len(custom_events) == 1
    assert custom_events[0]["alert"] == "ROAD_ICE_DETECTED"


def test_subprocess_transport_pure_facade_orchestration():
    mock_mgr = MagicMock(spec=GoBinaryManager)
    mock_mgr.bin_path = "/tmp/mock-bin"
    mock_mgr.ensure_ready.return_value = True

    mock_proc = MagicMock(spec=GoPipeProcess)
    mock_proc.is_running = False
    mock_proc.spawn.return_value = True
    mock_proc.stdout = MagicMock()
    mock_proc.stderr = MagicMock()

    mock_dispatcher = MagicMock(spec=GoPipeDispatcher)

    transport = GoSubprocessTransport(
        binary_manager=mock_mgr,
        process=mock_proc,
        dispatcher=mock_dispatcher,
    )

    # Conforms to protocol
    assert isinstance(transport, IGatewayTransport)

    # Start facade
    cb = MagicMock()
    assert transport.start(cb) is True

    mock_mgr.ensure_ready.assert_called_once()
    mock_dispatcher.set_packet_callback.assert_called_once_with(cb)
    mock_proc.spawn.assert_called_once()
    mock_dispatcher.start.assert_called_once()

    # Send command
    mock_proc.is_running = True
    transport.send_command({"cmd": "PING"})
    mock_proc.write_line.assert_called_once_with('{"cmd": "PING"}')

    # Stop facade
    mock_proc.is_running = True
    transport.stop()
    mock_proc.terminate_gracefully.assert_called_once()
    mock_dispatcher.stop.assert_called_once()


def test_go_push_adapter_dependency_inversion():
    """
    Asserts Dependency Inversion Principle: GoPushAdapter can receive any mock IGatewayTransport.
    """
    mock_transport = MagicMock(spec=IGatewayTransport)
    mock_transport.is_running = False

    adapter = GoPushAdapter(transport=mock_transport)
    assert adapter.transport is mock_transport

    adapter.start(lambda sid, p, m: None)
    mock_transport.start.assert_called_once()

    adapter.stop()
    mock_transport.stop.assert_called_once()
