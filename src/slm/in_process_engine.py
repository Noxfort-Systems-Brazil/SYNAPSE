# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
import gc
import logging
from typing import Dict, Any, Optional, Tuple
import torch

from src.services.prompt_registry import PromptRegistry
from src.slm.device_manager import SLMDeviceManager
from src.slm.model_loader import SLMModelLoader
from src.slm.output_sanitizer import SLMOutputSanitizer
from src.slm.prompt_builder import SLMPromptBuilder

logger = logging.getLogger("SLM.InProcessEngine")


class InProcessJuristEngine:
    """Manages in-process loading, memory freeing, and inference for SLM models."""

    @staticmethod
    def load(
        model_id: str,
        is_gguf: bool,
        device: str = "auto",
        gpu_layers: int = 16
    ) -> Tuple[Optional[Any], Optional[Any], str]:
        """Loads GGUF or HuggingFace model into memory."""
        logger.info(f"Loading SLM on-demand from: {model_id}")
        if is_gguf:
            device_setting, resolved_layers = SLMDeviceManager.resolve_device_settings(device, gpu_layers)
            model = SLMModelLoader.load_model(
                model_path=model_id,
                device_setting=device_setting,
                gpu_layers=resolved_layers,
                n_ctx=2048
            )
            return model, None, device_setting
        else:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            is_local = os.path.isdir(model_id)
            tokenizer = AutoTokenizer.from_pretrained(model_id, local_files_only=is_local)
            model = AutoModelForCausalLM.from_pretrained(
                model_id,
                device_map="auto",
                torch_dtype=torch.float16,
                trust_remote_code=True,
                local_files_only=is_local
            )
            return model, tokenizer, "auto"

    @staticmethod
    def unload(model: Optional[Any], tokenizer: Optional[Any]) -> None:
        """Frees VRAM/RAM by destroying model instance and calling gc.collect."""
        if model is not None:
            close_fn = getattr(model, 'close', None)
            cpu_fn = getattr(model, 'cpu', None)
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
            del model

        del tokenizer
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    @classmethod
    def generate_report(
        cls,
        model: Any,
        tokenizer: Any,
        is_gguf: bool,
        tensor_data: Dict[str, Any],
        timestamp: str,
        locale: str,
        target: str,
        device_str: str
    ) -> str:
        if is_gguf:
            messages = SLMPromptBuilder.build_xai_chat_messages(
                target=target,
                attribution_map=tensor_data,
                timestamp=timestamp,
                locale=locale
            )
            response_dict = model.create_chat_completion(
                messages=messages,
                max_tokens=600,
                temperature=0.0
            )
            raw = response_dict["choices"][0]["message"]["content"] or ""
        else:
            values_summary = [f"{k}: {v}" for k, v in tensor_data.items()]
            context_data = {
                "source_id": target,
                "status": "INVESTIGATION_FLAGGED",
                "values": values_summary,
                "language": locale,
                "timestamp": timestamp
            }
            raw = cls.generate_verdict(model, tokenizer, is_gguf, context_data, device_str)

        return SLMOutputSanitizer.sanitize(raw)

    @classmethod
    def generate_verdict(
        cls,
        model: Any,
        tokenizer: Any,
        is_gguf: bool,
        context_data: Dict[str, Any],
        device_str: str
    ) -> str:
        messages = PromptRegistry.build_messages(
            source=context_data.get('source_id', 'Unknown'),
            status=context_data.get('status', 'NORMAL'),
            values=context_data.get('values', []),
            language=context_data.get('language', 'pt_BR')
        )

        if is_gguf:
            try:
                response_dict = model.create_chat_completion(
                    messages=messages,
                    max_tokens=256,
                    temperature=0.0
                )
                raw = response_dict["choices"][0]["message"]["content"] or ""
            except Exception as e:
                logger.error(f"GGUF generation failed: {e}")
                return f"Erro na inferência do Jurista: {e}"
        else:
            device = torch.device(device_str if device_str != "auto" else "cpu")
            text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            model_inputs = tokenizer([text], return_tensors="pt").to(device)

            with torch.no_grad():
                generated_ids = model.generate(
                    **model_inputs,
                    max_new_tokens=256,
                    temperature=0.0,
                    do_sample=False
                )

            generated_ids = [
                output_ids[len(input_ids):]
                for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
            ]
            raw = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

        cleaned = PromptRegistry.clean_response(raw)
        return SLMOutputSanitizer.sanitize(cleaned)
