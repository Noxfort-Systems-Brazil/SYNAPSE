# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Unit tests for EpisodicAuditRepository physics violations recording and ranked residual queries.
"""

from src.repositories.sensor_dictionary_repo import SensorDictionaryRepository
from src.repositories.episodic_audit_repo import EpisodicAuditRepository


def test_episodic_audit_repository(temp_db_engine):
    """Verifies recording physics violations and retrieving hardest episodes."""
    dict_repo = SensorDictionaryRepository(temp_db_engine)
    audit_repo = EpisodicAuditRepository(temp_db_engine, dict_repo)

    ep_id1 = audit_repo.record_episode(
        sensor_id="sensor_loop_01",
        anomaly_score=0.88,
        physics_residual=12.45,
        state_vector=[35.0, 42.0, 120.0],
        xai_verdict="Violação de conservação de fluxo LWR detectada na via JK.",
        metadata={"cause": "shockwave"}
    )
    assert ep_id1 is not None

    ep_id2 = audit_repo.record_episode(
        sensor_id="sensor_loop_02",
        anomaly_score=0.95,
        physics_residual=28.10,
        state_vector=[10.0, 15.0, 80.0],
        xai_verdict="Sensor travado em valor anômalo com resíduo crítico.",
        metadata={"cause": "stuck_sensor"}
    )
    assert ep_id2 is not None

    hardest = audit_repo.get_hardest_violations(top_k=5)
    assert len(hardest) == 2
    # The highest residual (28.10) must be first
    assert hardest[0]["physics_residual"] == 28.10
    assert hardest[0]["sensor_id"] == "sensor_loop_02"
