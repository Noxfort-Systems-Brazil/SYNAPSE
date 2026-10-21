# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from abc import ABC, abstractmethod
from typing import Callable, Dict, Any

class BaseStage(ABC):
    """
    Abstract Base Class representing a single, isolated step in the Offline Pipeline.
    
    Adheres strictly to SOLID principles:
    - SRP: Each child class implements only ONE specific domain logic.
    - OCP: New stages can be added to the pipeline without modifying existing ones.
    - DIP: The orchestrator (offline_service.py) depends on this abstraction, 
           not on the concrete heavy implementations.
    """

    def __init__(
        self, 
        synapse_root: str,
        log_cb: Callable[[str], None] = None, 
        progress_cb: Callable[[int], None] = None,
        check_stop_cb: Callable[[], bool] = None
    ):
        """
        Initializes the stage with common infrastructure dependencies.
        
        Args:
            synapse_root: Root directory of the system data.
            log_cb: Callback to emit log messages back to the UI.
            progress_cb: Callback to emit progress updates.
            check_stop_cb: Callback to verify if the process was interrupted by the user.
        """
        self.synapse_root = synapse_root
        
        # Fallback to empty lambdas if no callbacks are provided to avoid crashes
        self.log = log_cb or (lambda msg: None)
        self.progress = progress_cb or (lambda p: None)
        self.should_stop = check_stop_cb or (lambda: False)

    @abstractmethod
    def execute(self, shared_context: Dict[str, Any]) -> bool:
        """
        Executes the business logic for this specific stage.
        
        Args:
            shared_context: A dictionary passed along the pipeline stages 
                            to share state (e.g., paths, validated flags, dataframes) 
                            without tight coupling between stages.
                            
        Returns:
            bool: True if the stage completed successfully (continue pipeline), 
                  False if it failed or was skipped intentionally.
        """
        pass

    def check_interruption(self) -> bool:
        """Helper to quickly check and log if the user stopped the pipeline."""
        if self.should_stop():
            self.log(f"[{self.__class__.__name__}] 🛑 Process interrupted by user.")
            return True
        return False
