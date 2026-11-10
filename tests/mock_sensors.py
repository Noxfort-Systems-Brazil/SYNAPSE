# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import sys
import os
import time

# Allow importing from root directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PyQt6.QtCore import QCoreApplication
from src.factories.controller_factory import ControllerFactory

def run_stress_test(num_sensors):
    app = QCoreApplication(sys.argv)
    app.setApplicationName("SYNAPSE_STRESS")
    
    print(f"\n[Stress Test] Inicializando MainController via ControllerFactory...")
    controller = ControllerFactory.create_main_controller()
    
    print(f"[Stress Test] Registrando {num_sensors} sensores mock na pipeline (SourceType: API)...")
    for i in range(num_sensors):
        # Register mock sensors so engine, ingestors and optimizers act upon them
        controller.project.add_data_source(f"Sensor_Mock_{i}", "API", f"mock://sensor_{i}")
        
    print("[Stress Test] Disparando start_online_operation()...")
    # This starts all services: Ingestors, Inference Engines and Threads
    controller.system.start_online_operation()
    
    print("[Stress Test] Pipeline completamente engajada. Event loop ativo.")
    sys.exit(app.exec())

if __name__ == "__main__":
    try:
        num_sensors = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    except ValueError:
        num_sensors = 10
        
    run_stress_test(num_sensors)
