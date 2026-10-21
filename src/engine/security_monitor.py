# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import time
from typing import Dict, Any, Optional
from src.utils.logging_setup import logger

class SecurityMonitor:
    """
    Analyzes the outputs of the Auditor Autoencoder.
    Adheres to the Single Responsibility Principle (SRP) by keeping thresholding
    and alert payload generation away from the cycle math logic.
    """
    
    def __init__(self, threshold: float = 0.85):
        self.threshold = threshold
        
    def evaluate(self, security_score: float, threshold: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        Evaluates the Security Score against defined thresholds and returns an alert payload if triggered.
        """
        active_threshold = threshold if threshold is not None else self.threshold
        if security_score > active_threshold:
            logger.warning(
                f"[Auditor] 🛡️ Security Violation / Anomaly Detected! "
                f"Score: {security_score:.4f} (Threshold: {active_threshold:.4f})"
            )
            
            return {
                "title": "Integrity Violation",
                "payload": {
                    "loss": security_score,
                    "threshold": active_threshold,
                    "status": "ATTACK",
                    "timestamp": time.time()
                }
            }
            
        return None
