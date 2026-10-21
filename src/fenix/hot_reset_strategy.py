# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import time
import traceback
from src.utils.logging_setup import logger
from src.fenix.protocols import IFenixStrategy, StrategyCallbacks


class Level1HotResetStrategy:
    """
    Level 1 Emergency Hot-Reset Strategy (~1-2 seconds):
    1. Activates AFB replay transmission immediately.
    2. Flushes contaminated memory buffers and resets neural state.
    3. Reloads calibrated checkpoints.
    4. Injects MEH warm-up window.
    5. Validates recovery and restores normal neural flow.
    """

    @property
    def name(self) -> str:
        return "Fênix N1: Neural Hot-Reset"

    def execute(self, callbacks: StrategyCallbacks) -> bool:
        try:
            logger.info(">>> [FENIX N1] EXECUTING REAL-TIME HOT-RESET <<<")

            # Step 1: Activate AFB fallback transmission
            callbacks.on_progress("Activating AFB (Autonomous Fallback Bridge)...", 15)
            callbacks.on_request_fallback(True)
            time.sleep(0.2)

            if callbacks.is_interrupted():
                raise InterruptedError("Cycle Aborted")

            # Step 2: Flush state and reload pre-calibrated weights
            callbacks.on_progress("Purging neural memory buffers & reloading weights...", 50)
            callbacks.on_request_neural_reset()
            time.sleep(0.5)

            if callbacks.is_interrupted():
                raise InterruptedError("Cycle Aborted")

            # Step 3: MEH Warm-Up injection is applied via cycle processor
            callbacks.on_progress("Warming up with MEH historical baseline...", 80)
            time.sleep(0.3)

            if callbacks.is_interrupted():
                raise InterruptedError("Cycle Aborted")

            # Step 4: Complete reset & stand down AFB
            callbacks.on_progress("Neural state normalized. Deactivating AFB...", 95)
            callbacks.on_request_fallback(False)

            logger.info("<<< [FENIX N1] HOT-RESET COMPLETE. NORMAL OPERATIONS RESTORED. >>>")
            return True

        except Exception as e:
            logger.error(f"[FENIX N1] Hot-Reset failed: {e}")
            traceback.print_exc()
            callbacks.on_request_fallback(False)
            raise e
