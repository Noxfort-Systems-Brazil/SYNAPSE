# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import pytest
import time
from unittest.mock import MagicMock, patch
from src.slm.process.isolated_jurist_manager import IsolatedJuristManager
from src.slm.process.llm_worker_process import LLMWorkerInstance


def test_llm_worker_instance_mock_inference():
    worker = LLMWorkerInstance(model_id="mock_model.gguf")
    assert worker.is_loaded is False

    # Simulate mock model
    mock_llm = MagicMock()
    mock_llm.create_chat_completion.return_value = {
        "choices": [{"message": {"content": "<think>pensamento pericial</think>Laudo pericial aprovado sem irregularidades."}}]
    }
    worker._model = mock_llm
    worker._is_loaded = True

    # Test report generation with output sanitization
    report_text = worker.generate_report({
        "tensor_data": {"fluxo": 120.0, "velocidade": 45.0},
        "target": "AUDITOR_XAI",
        "locale": "pt_BR",
        "auto_unload": False,
    })

    assert "Laudo pericial aprovado" in report_text
    assert "<think>" not in report_text
    assert "</think>" not in report_text

    # Test verdict generation
    verdict_text = worker.generate_verdict({
        "source_id": "sensor_det_01",
        "status": "NORMAL",
        "values": ["fluxo: 120"],
        "auto_unload": False,
    })
    assert "Laudo pericial aprovado" in verdict_text

    # Test unload
    res = worker.unload_resources()
    assert res["unloaded"] is True
    assert worker.is_loaded is False


def test_isolated_jurist_manager_lifecycle():
    manager = IsolatedJuristManager(model_id="test_model.gguf", command_timeout=5.0)
    assert manager.is_alive is False

    # Test that send_command handles simulated communication
    mock_conn = MagicMock()
    mock_conn.poll.return_value = True
    mock_conn.recv.return_value = {"id": "test_id", "success": True, "result": "pong"}

    manager._parent_conn = mock_conn
    mock_proc = MagicMock()
    mock_proc.is_alive.return_value = True
    manager._process = mock_proc

    with patch("uuid.uuid4", return_value="test_id"):
        res = manager.send_command("ping")
        assert res == "pong"

    # Test shutdown
    manager.shutdown()
    assert manager._parent_conn is None
    assert manager._process is None
    assert manager.is_alive is False


def test_isolated_jurist_manager_connection_reset_handling():
    manager = IsolatedJuristManager(model_id="test_model.gguf", command_timeout=2.0)
    mock_conn = MagicMock()
    mock_conn.poll.return_value = True
    mock_conn.recv.side_effect = ConnectionResetError(104, "Connection reset by peer")

    manager._parent_conn = mock_conn
    mock_proc = MagicMock()
    mock_proc.is_alive.return_value = True
    manager._process = mock_proc

    report = manager.generate_report(tensor_data={"f": 1.0}, auto_unload=True)
    assert "Erro: Inferência da LLM em processo isolado falhou" in report
    assert "IPC Pipe broken" in report or "Connection reset" in report
    # Ensure manager cleaned up
    assert manager._parent_conn is None
    assert manager._process is None


def test_isolated_jurist_manager_concurrency():
    import concurrent.futures

    manager = IsolatedJuristManager(model_id="test_model.gguf", command_timeout=5.0)

    results = []

    def fake_send_command(cmd, payload=None, timeout=None):
        time.sleep(0.05)
        return f"Report for {payload.get('target', 'unknown')}"

    with patch.object(manager, "send_command", side_effect=fake_send_command):
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futs = [
                executor.submit(
                    manager.generate_report,
                    tensor_data={"val": i},
                    target=f"Target_{i}",
                    auto_unload=True,
                )
                for i in range(5)
            ]
            for f in concurrent.futures.as_completed(futs):
                results.append(f.result())

    assert len(results) == 5
    for i in range(5):
        assert any(f"Report for Target_{i}" in r for r in results)
