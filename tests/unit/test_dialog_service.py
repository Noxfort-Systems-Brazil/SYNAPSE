# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
from unittest.mock import MagicMock, patch
import pytest

from src.infrastructure.dialog_service import NativeDialogService
from src.handlers.dialog_handler import SystemDialogHandler
from src.ipc.ipc_protocol import IpcMessage


def test_native_dialog_service_save_file_zenity():
    service = NativeDialogService()
    with patch("sys.platform", "linux"):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="/home/user/meu_laudo.docx\n")
            res = service.save_file(default_filename="laudo.docx", title="Salvar Laudo", file_filter="*.docx")
            assert res == "/home/user/meu_laudo.docx"
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert "zenity" in args
            assert "--save" in args
            assert "--filename=laudo.docx" in args


def test_native_dialog_service_save_file_cancelled():
    service = NativeDialogService()
    with patch("sys.platform", "linux"):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="")
            res = service.save_file(default_filename="laudo.docx")
            assert res is None


def test_native_dialog_service_pick_directory():
    service = NativeDialogService()
    with patch("sys.platform", "linux"):
        with patch("subprocess.run") as mock_run:
            with patch("os.path.isdir", return_value=True):
                mock_run.return_value = MagicMock(returncode=0, stdout="/home/user/Documentos\n")
                res = service.pick_directory(title="Escolher Pasta")
                assert res == "/home/user/Documentos"
                args = mock_run.call_args[0][0]
                assert "zenity" in args
                assert "--directory" in args


def test_dialog_handler_save_file_and_pick_directory():
    mock_service = MagicMock()
    mock_service.save_file.return_value = "/tmp/laudo_teste.docx"
    mock_service.pick_directory.return_value = "/tmp"

    handler = SystemDialogHandler(dialog_service=mock_service)

    msg_save = IpcMessage(action="save_file", payload={"title": "Salvar", "default_filename": "laudo.docx"})
    res_save = handler.handle_save_file(msg_save)
    assert res_save == {"path": "/tmp/laudo_teste.docx", "cancelled": False}

    msg_pick_dir = IpcMessage(action="pick_directory", payload={"title": "Selecionar"})
    res_pick_dir = handler.handle_pick_directory(msg_pick_dir)
    assert res_pick_dir == {"path": "/tmp", "cancelled": False}


def test_report_handler_custom_output_path(tmp_path):
    from src.handlers.report_handler import ReportCommandHandler

    mock_service = MagicMock()
    mock_service.export_docx.side_effect = lambda report_data, output_path, typography_options: output_path

    handler = ReportCommandHandler(report_service=mock_service)


    report_payload = {
        "protocol": "EXP-2026-TEST",
        "title": "Laudo Pericial Teste",
    }

    # Case 1: Custom path with .docx
    custom_target = str(tmp_path / "meu_laudo_custom.docx")
    msg1 = IpcMessage(
        action="export_official_report_docx",
        payload={"report": report_payload, "output_path": custom_target},
    )
    res1 = handler.handle_export_official_report_docx(msg1)
    assert res1["success"] is True
    assert res1["output_path"] == custom_target

    # Case 2: Custom path without .docx -> should append .docx
    custom_no_ext = str(tmp_path / "meu_laudo_sem_ext")
    msg2 = IpcMessage(
        action="export_official_report_docx",
        payload={"report": report_payload, "output_path": custom_no_ext},
    )
    res2 = handler.handle_export_official_report_docx(msg2)
    assert res2["success"] is True
    assert res2["output_path"] == f"{custom_no_ext}.docx"

    # Case 3: Output path is an existing directory -> should save inside directory
    dir_target = str(tmp_path)
    msg3 = IpcMessage(
        action="export_official_report_docx",
        payload={"report": report_payload, "output_path": dir_target},
    )
    res3 = handler.handle_export_official_report_docx(msg3)
    assert res3["success"] is True
    expected_inside_dir = os.path.join(dir_target, "Laudo_Tecnico_Trafego_EXP-2026-TEST.docx")
    assert res3["output_path"] == expected_inside_dir

    # Case 4: Output path is None -> default to Downloads
    msg4 = IpcMessage(
        action="export_official_report_docx",
        payload={"report": report_payload, "output_path": None},
    )
    res4 = handler.handle_export_official_report_docx(msg4)
    assert res4["success"] is True
    assert "Downloads" in res4["output_path"]
    assert "Laudo_Tecnico_Trafego_EXP-2026-TEST.docx" in res4["output_path"]

