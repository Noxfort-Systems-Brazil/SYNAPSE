# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Any, Dict, List, Optional

from src.interfaces.xai import IXAIReporter, IXAIStrategy
from src.agents.jurist_agent import JuristAgent
from src.utils.logging_setup import get_logger

logger = get_logger("XAI.ReporterService")


class XAIReporterService(IXAIReporter):
    """
    Semantic Reporting Service for XAI.
    Manages Jurist on-demand SLM lifecycle and provides seamless fallback to model strategy reports.
    Single-process and zero-VRAM-leakage architecture.
    """

    def __init__(self, jurist: Optional[JuristAgent] = None, auto_load_jurist: bool = True):
        self._jurist = jurist
        self._auto_load_jurist = auto_load_jurist

    @property
    def jurist(self) -> Optional[JuristAgent]:
        return self._jurist

    def _ensure_jurist_ready(self) -> None:
        """Ensures Jurist Agent instance is ready for on-demand dispatch."""
        if self._jurist is None and self._auto_load_jurist:
            try:
                self._jurist = JuristAgent()
            except Exception as e:
                logger.error(f"Failed to instantiate JuristAgent: {e}", exc_info=True)
                self._jurist = None

    def generate_report(
        self,
        target: str,
        attr_list: List[float],
        feature_names: List[str],
        timestamp: str,
        delta: float,
        strategy: Optional[IXAIStrategy] = None
    ) -> str:
        """
        Generates human-readable semantic interpretation text.
        Delegates to Jurist on-demand SLM if available, with immediate fallback to strategy reports.
        """
        self._ensure_jurist_ready()

        resolved_names = feature_names if feature_names else [f"F{i}" for i in range(len(attr_list))]
        attribution_map = dict(zip(resolved_names, attr_list))
        sig_map = {k: v for k, v in attribution_map.items() if abs(v) > 0.001}
        if not sig_map:
            sig_map = attribution_map

        if self._jurist is not None:
            try:
                slm_payload: Dict[str, Any] = sig_map
                if len(sig_map) > 25:
                    sorted_items = sorted(sig_map.items(), key=lambda kv: abs(float(kv[1])), reverse=True)
                    top_items = {k: round(float(v), 4) for k, v in sorted_items[:25]}
                    vals = [float(v) for v in sig_map.values()]
                    top_items["_summary"] = {
                        "total_features_analyzed": len(attr_list),
                        "significant_features": len(sig_map),
                        "shown_top_k": 25,
                        "max_attribution": round(max(vals), 4),
                        "min_attribution": round(min(vals), 4),
                        "convergence_delta": round(float(delta), 5),
                    }
                    slm_payload = top_items
                else:
                    slm_payload = {
                        k: (round(float(v), 4) if isinstance(v, (int, float)) else v)
                        for k, v in sig_map.items()
                    }

                report_text = self._jurist.generate_report(
                    tensor_data=slm_payload,
                    timestamp=timestamp,
                    locale="pt_BR",
                    target=target,
                    auto_unload=True
                )
                if report_text and not report_text.startswith("Erro:"):
                    return report_text
                else:
                    logger.warning(f"Jurist returned error or empty text: '{report_text}'. Triggering strategy fallback.")
            except Exception as e_gen:
                logger.error(f"Jurist Generation Error: {e_gen}", exc_info=True)

        # Resilient fallback to mathematical/domain strategy template
        if strategy:
            return strategy.generate_fallback_text(
                delta=delta,
                sig_map=sig_map,
                attr_list=attr_list
            )

        return (
            f"Análise XAI ({target}): Concluída com delta {delta:.4f} em {len(attr_list)} features."
        )

    def unload_resources(self) -> None:
        """Releases Jurist SLM VRAM."""
        if self._jurist is not None:
            logger.info("Unloading Jurist SLM resources from ReporterService.")
            try:
                self._jurist.unload_resources()
            except Exception as e:
                logger.warning(f"Error unloading Jurist resources: {e}")
            finally:
                self._jurist = None
