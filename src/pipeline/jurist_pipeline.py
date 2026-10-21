# SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
# Copyright (C) 2026 Noxfort Systems
#
# File: src/pipeline/jurist_pipeline.py
# Description: Pure Orchestrator Pipeline for Jurist SLM Execution (SOLID / Clean Architecture).

import threading
from typing import Dict, Any, Optional

import torch

from src.interfaces.pipelines import IJuristPipeline
from src.slm.process.isolated_jurist_manager import IsolatedJuristManager
from src.slm.in_process_engine import InProcessJuristEngine
from src.utils.logging_setup import get_logger
from src.utils.model_paths import get_qwen_gguf_path
from src.slm.model_loader import SLMModelLoader

logger = get_logger("Pipeline.Jurist")


class JuristPipeline(IJuristPipeline):
    """
    On-Demand SLM Execution & Technical-Legal Reasoning Pipeline.

    Pure Orchestrator:
    - Fault-Domain Isolation: delegates to IsolatedJuristManager (out-of-process) by default.
    - Fallback: delegates in-process execution to InProcessJuristEngine.
    """

    def __init__(self, model_id: Optional[str] = None, isolated: bool = True):
        self.model_id = model_id or get_qwen_gguf_path()
        self.isolated = isolated
        self.is_gguf = str(self.model_id).endswith(".gguf")
        self._lock = threading.RLock()
        self._device = "cpu"

        # In-process state
        self.tokenizer: Optional[Any] = None
        self._model: Optional[Any] = None
        self._is_loaded = False

        # Out-of-process manager
        self._isolated_manager = (
            IsolatedJuristManager(model_id=self.model_id) if self.isolated else None
        )

    @property
    def is_loaded(self) -> bool:
        if self.isolated and self._isolated_manager:
            return self._isolated_manager.is_loaded
        return self._is_loaded and self._model is not None

    @property
    def model(self) -> Optional[Any]:
        return self._model

    def to(self, device: torch.device) -> 'JuristPipeline':
        self._device = str(device)
        return self

    def load_resources(self, device: str = "auto", gpu_layers: int = 16) -> None:
        """Loads the SLM model into memory on demand."""
        if self.is_loaded:
            return

        if self.isolated and self._isolated_manager:
            self._isolated_manager.load_resources(device=device, gpu_layers=gpu_layers)
            return

        with self._lock:
            try:
                if self.is_gguf:
                    from src.slm.device_manager import SLMDeviceManager
                    device_setting, resolved_layers = SLMDeviceManager.resolve_device_settings(device, gpu_layers)
                    self._model = SLMModelLoader.load_model(
                        model_path=self.model_id,
                        device_setting=device_setting,
                        gpu_layers=resolved_layers,
                        n_ctx=2048
                    )
                    self.tokenizer = None
                    self._device = device_setting
                else:
                    self._model, self.tokenizer, self._device = InProcessJuristEngine.load(
                        model_id=self.model_id,
                        is_gguf=self.is_gguf,
                        device=device,
                        gpu_layers=gpu_layers
                    )
                self._is_loaded = True
            except Exception as e:
                logger.error(f"[JuristPipeline] Failed to load SLM ({self.model_id}): {e}", exc_info=True)
                self._is_loaded = False
                self._model = None

    def unload_resources(self) -> None:
        """Frees VRAM/RAM by destroying the model instance and clearing GPU cache."""
        if self.isolated and self._isolated_manager:
            self._isolated_manager.unload_resources()
            return

        with self._lock:
            InProcessJuristEngine.unload(self._model, self.tokenizer)
            self._model = None
            self.tokenizer = None
            self._is_loaded = False

    def generate_report(
        self,
        tensor_data: Dict[str, Any],
        timestamp: str = "",
        locale: str = "pt_BR",
        target: str = "XAI_Attribution",
        auto_unload: bool = True,
        **kwargs: Any
    ) -> str:
        """Executes on-demand XAI narrative synthesis."""
        if self.isolated and self._isolated_manager:
            return self._isolated_manager.generate_report(
                tensor_data=tensor_data,
                timestamp=timestamp,
                locale=locale,
                target=target,
                auto_unload=auto_unload,
                **kwargs
            )

        with self._lock:
            try:
                if not self.is_loaded:
                    self.load_resources()

                if not self.is_loaded or self._model is None:
                    return "Erro: Modelo Jurista não pôde ser carregado do Model_Vault."

                return InProcessJuristEngine.generate_report(
                    model=self._model,
                    tokenizer=self.tokenizer,
                    is_gguf=self.is_gguf,
                    tensor_data=tensor_data,
                    timestamp=timestamp,
                    locale=locale,
                    target=target,
                    device_str=self._device
                )
            finally:
                if auto_unload:
                    self.unload_resources()

    def generate(self, context_data: Dict[str, Any], auto_unload: bool = False) -> str:
        """Executes general verdict generation with prompt formatting and post-cleaning."""
        if self.isolated and self._isolated_manager:
            return self._isolated_manager.generate(
                context_data=context_data,
                auto_unload=auto_unload
            )

        with self._lock:
            try:
                if not self.is_loaded:
                    self.load_resources()

                if not self.is_loaded or self._model is None:
                    return "Erro: Modelo Jurista não pôde ser carregado do Model_Vault."

                return InProcessJuristEngine.generate_verdict(
                    model=self._model,
                    tokenizer=self.tokenizer,
                    is_gguf=self.is_gguf,
                    context_data=context_data,
                    device_str=self._device
                )
            finally:
                if auto_unload:
                    self.unload_resources()
