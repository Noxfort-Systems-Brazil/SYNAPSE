# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
import gc
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("LLM.WorkerInstance")


class LLMWorkerInstance:
    """
    Stateful inference worker instance running inside the dedicated subprocess.
    """

    def __init__(self, model_id: str, device: str = "auto", gpu_layers: int = 16):
        self.model_id = model_id
        self.default_device = device
        self.default_gpu_layers = gpu_layers
        self.is_gguf = str(model_id).endswith(".gguf")
        self._model: Optional[Any] = None
        self._tokenizer: Optional[Any] = None
        self._is_loaded = False
        self._active_device = "cpu"

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded and self._model is not None

    def load_resources(self, device: Optional[str] = None, gpu_layers: Optional[int] = None) -> Dict[str, Any]:
        """Loads model into isolated process memory."""
        if self.is_loaded:
            return {"loaded": True, "device": self._active_device, "cached": True}

        target_device = device or self.default_device
        target_layers = gpu_layers if gpu_layers is not None else self.default_gpu_layers

        logger.info(f"Loading SLM in isolated worker (PID={os.getpid()}) from: {self.model_id}")

        if self.is_gguf:
            from src.slm.device_manager import SLMDeviceManager
            from src.slm.model_loader import SLMModelLoader

            device_setting, resolved_layers = SLMDeviceManager.resolve_device_settings(target_device, target_layers)
            self._model = SLMModelLoader.load_model(
                model_path=self.model_id,
                device_setting=device_setting,
                gpu_layers=resolved_layers,
                n_ctx=4096,
            )
            self._tokenizer = None
            self._is_loaded = True
            self._active_device = device_setting
            logger.info(f"GGUF SLM loaded in isolated worker (device={device_setting}, layers={resolved_layers}).")
        else:
            import torch
            from transformers import AutoTokenizer, AutoModelForCausalLM

            is_local = os.path.isdir(self.model_id)
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_id, local_files_only=is_local)
            self._model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                device_map="auto",
                torch_dtype=torch.float16,
                trust_remote_code=True,
                local_files_only=is_local,
            )
            self._is_loaded = True
            self._active_device = "auto"
            logger.info("HuggingFace LLM loaded in isolated worker (FP16).")

        return {"loaded": True, "device": self._active_device, "cached": False}

    def unload_resources(self) -> Dict[str, Any]:
        """Releases all model references and clears GPU cache."""
        if not self._is_loaded and self._model is None:
            return {"unloaded": True, "was_empty": True}

        logger.info("Unloading SLM in isolated worker to release resources...")
        if self._model is not None:
            close_fn = getattr(self._model, "close", None)
            cpu_fn = getattr(self._model, "cpu", None)
            if callable(close_fn):
                try:
                    close_fn()
                except Exception:
                    pass
            elif callable(cpu_fn):
                try:
                    cpu_fn()
                except Exception:
                    pass
            del self._model

        self._model = None
        self._tokenizer = None
        self._is_loaded = False

        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass

        return {"unloaded": True}

    def clear_cache(self) -> Dict[str, Any]:
        """Evicts transient KV/activation VRAM caches while keeping loaded model weights resident."""
        gc.collect()
        cuda_cleared = False
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                cuda_cleared = True
        except Exception:
            pass
        return {"cache_cleared": True, "cuda_cleared": cuda_cleared, "loaded": self.is_loaded}

    def generate_report(self, payload: Dict[str, Any]) -> str:
        """Synthesizes an XAI narrative report."""
        from src.slm.output_sanitizer import SLMOutputSanitizer
        from src.slm.prompt_builder import SLMPromptBuilder

        auto_unload = payload.get("auto_unload", False)
        tensor_data = payload.get("tensor_data", {})
        timestamp = payload.get("timestamp", "")
        locale = payload.get("locale", "pt_BR")
        target = payload.get("target", "XAI_Attribution")
        max_tokens = payload.get("max_tokens", 600)
        temperature = payload.get("temperature", 0.0)

        try:
            if not self.is_loaded:
                self.load_resources()

            if not self.is_loaded or self._model is None:
                return "Erro: Modelo Jurista não pôde ser carregado no processo isolado."

            if self.is_gguf:
                messages = SLMPromptBuilder.build_xai_chat_messages(
                    target=target,
                    attribution_map=tensor_data,
                    timestamp=timestamp,
                    locale=locale,
                )
                response_dict = self._model.create_chat_completion(
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                raw_response = response_dict["choices"][0]["message"]["content"] or ""
            else:
                values_summary = [f"{k}: {v}" for k, v in tensor_data.items()]
                context_data = {
                    "source_id": target,
                    "status": "INVESTIGATION_FLAGGED",
                    "values": values_summary,
                    "language": locale,
                    "timestamp": timestamp,
                }
                raw_response = self.generate_verdict(context_data)

            return SLMOutputSanitizer.sanitize(raw_response)

        finally:
            if auto_unload:
                self.unload_resources()
            else:
                self.clear_cache()

    def generate_verdict(self, payload: Dict[str, Any]) -> str:
        """Generates general technical-legal verdict on traffic data."""
        from src.slm.output_sanitizer import SLMOutputSanitizer
        from src.services.prompt_registry import PromptRegistry

        auto_unload = payload.get("auto_unload", False)
        max_tokens = payload.get("max_tokens", 256)
        temperature = payload.get("temperature", 0.0)

        try:
            if not self.is_loaded:
                self.load_resources()

            if not self.is_loaded or self._model is None:
                return "Erro: Modelo Jurista não pôde ser carregado no processo isolado."

            messages = PromptRegistry.build_messages(
                source=payload.get("source_id", "Unknown"),
                status=payload.get("status", "NORMAL"),
                values=payload.get("values", []),
                language=payload.get("language", "pt_BR"),
            )

            if self.is_gguf:
                response_dict = self._model.create_chat_completion(
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                raw_response = response_dict["choices"][0]["message"]["content"] or ""
            else:
                import torch
                device = torch.device(self._active_device if self._active_device != "auto" else "cpu")
                text = self._tokenizer.apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=True
                )
                model_inputs = self._tokenizer([text], return_tensors="pt").to(device)

                with torch.no_grad():
                    generated_ids = self._model.generate(
                        **model_inputs,
                        max_new_tokens=max_tokens,
                        temperature=temperature,
                        do_sample=False,
                    )
                generated_ids = [
                    output_ids[len(input_ids):]
                    for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
                ]
                raw_response = self._tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

            cleaned = PromptRegistry.clean_response(raw_response)
            return SLMOutputSanitizer.sanitize(cleaned)

        finally:
            if auto_unload:
                self.unload_resources()
            else:
                self.clear_cache()
