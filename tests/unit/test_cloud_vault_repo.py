# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Unit tests for CloudVaultRepository syncing, fetching, and restoring BLOB checkpoints.
"""

from src.repositories.cloud_vault_repo import CloudVaultRepository


def test_cloud_vault_repository(temp_db_engine, tmp_path):
    """Verifies syncing and restoring neural checkpoints from PostgreSQL/SQLite BLOB."""
    vault = CloudVaultRepository(temp_db_engine)

    # Create a mock checkpoint file
    mock_ckpt = tmp_path / "models" / "best_hparams.pth"
    mock_ckpt.parent.mkdir(parents=True, exist_ok=True)
    dummy_content = b"SYNAPSE_NEURAL_WEIGHTS_VERSION_2_PAYLOAD_TEST_12345"
    mock_ckpt.write_bytes(dummy_content)

    # Sync to vault
    synced = vault.sync_file_to_vault(str(mock_ckpt), str(tmp_path))
    assert synced is True

    # Fetch bytes directly
    content = vault.fetch_file_from_vault("models/best_hparams.pth")
    assert content == dummy_content

    # Restore into another location
    restore_path = tmp_path / "restored" / "best_hparams.pth"
    restored = vault.restore_file_from_vault("models/best_hparams.pth", str(restore_path))
    assert restored is True
    assert restore_path.exists()
    assert restore_path.read_bytes() == dummy_content
