# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from dataclasses import dataclass
from src.physics.constants import STANDARD_GRAVITY, TYPICAL_MAX_ACCEL_MS2, TYPICAL_MAX_DECEL_MS2

# --- CONSTANTS & CONFIGURATION ---

GRAVITY = STANDARD_GRAVITY  # 9.80665 m/s^2 (International Standard CGPM / ISO 80000-3)
MAX_ACCEL = TYPICAL_MAX_ACCEL_MS2   # 4.5 m/s^2 (Typical vehicular acceleration)
MAX_DECEL = TYPICAL_MAX_DECEL_MS2  # -9.0 m/s^2 (Emergency braking)
FRICTION_DECAY = 0.95 # Damping factor for Dead Reckoning (Simulates air resistance/friction)

@dataclass
class SensorProfile:
    """
    Defines noise characteristics for different data sources.
    Crucial for tuning the Kalman Matrix R (Measurement Noise).
    """
    name: str
    r_val: float      # Measurement Noise (Higher = Trust Sensor Less)
    q_val: float      # Process Noise (Higher = Expect More Erratic Movement)
    gating_threshold: float # Mahalanobis Distance for outlier rejection

# Pre-defined profiles
PROFILES = {
    "DEFAULT": SensorProfile("Generic", r_val=5.0, q_val=0.1, gating_threshold=3.0),
    "CAMERA": SensorProfile("Vision", r_val=2.0, q_val=0.2, gating_threshold=2.5),
    "INDUCTIVE": SensorProfile("Loop", r_val=0.5, q_val=0.05, gating_threshold=4.0),
    "HISTORY": SensorProfile("Simulation", r_val=0.1, q_val=0.01, gating_threshold=10.0)
}

@dataclass
class KineticState:
    """Immutable snapshot of a physics entity."""
    p: float # Position
    v: float # Velocity
    a: float # Acceleration
    uncertainty: float # Trace of Covariance Matrix
    confidence: float  # Normalized 0.0 - 1.0
