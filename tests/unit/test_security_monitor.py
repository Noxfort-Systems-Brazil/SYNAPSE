# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import pytest
from src.engine.security_monitor import SecurityMonitor


def test_security_monitor_default_threshold():
    monitor = SecurityMonitor(threshold=0.75)
    
    # Below threshold -> No alert
    assert monitor.evaluate(0.50) is None
    assert monitor.evaluate(0.74) is None
    
    # Above threshold -> Alert
    alert = monitor.evaluate(0.80)
    assert alert is not None
    assert alert["title"] == "Integrity Violation"
    assert alert["payload"]["status"] == "ATTACK"
    assert alert["payload"]["loss"] == 0.80
    assert alert["payload"]["threshold"] == 0.75


def test_security_monitor_dynamic_threshold():
    monitor = SecurityMonitor(threshold=0.50)
    
    # Dynamic threshold overrides default threshold
    assert monitor.evaluate(0.60, threshold=0.75) is None
    
    alert = monitor.evaluate(0.80, threshold=0.75)
    assert alert is not None
    assert alert["payload"]["loss"] == 0.80
    assert alert["payload"]["threshold"] == 0.75
