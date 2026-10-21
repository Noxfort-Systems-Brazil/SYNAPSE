# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
import logging
import numpy as np
import torch
from typing import List, Optional, Any

from src.optimization.optimization_task import OptimizationTask

# Strategy Imports
from src.optimization.strategies_flow import FlowStrategies
from src.optimization.strategies_quality import QualityStrategies
from src.optimization.strategies_semantic import SemanticStrategies

# Geometric data handling for GATv2
try:
    from torch_geometric.data import Data
except ImportError:
    Data = None

logger = logging.getLogger("Synapse.TaskRegistry")


class TaskRegistry:
    """
    Factory that builds the ordered list of OptimizationTasks.
    
    Responsibilities (SRP):
    - Encapsulates ALL data preparation logic per agent.
    - Resolves conditional availability (map, cartographer, PyG).
    - Produces self-contained OptimizationTask objects with closures.
    
    The OptimizerService never touches strategies or data prep directly.
    """

    @staticmethod
    def build_tasks(
        univ_data: np.ndarray,
        map_graph: Optional[Any],
        map_file_path: Optional[str],
        device: torch.device,
        base_dir: str = ""
    ) -> List[OptimizationTask]:
        """
        Constructs the full optimization pipeline as a list of tasks.
        
        Args:
            univ_data: Numeric matrix [TimeSteps, Features] from golden parquet.
            map_graph: PyG Data object or dict from SUMO map (can be None).
            map_file_path: Path to .net.xml.gz file (can be None).
            device: Target torch device.
            base_dir: Synapse root for saving diplomas.
            
        Returns:
            Ordered list of OptimizationTask ready for sequential execution.
        """
        tasks: List[OptimizationTask] = []

        # ═══════════════════════════════════════════════════════════════
        # Phase 1: Spatial — Coordinator (GATv2)
        # ═══════════════════════════════════════════════════════════════
        if map_graph is not None:
            clean_graph = TaskRegistry._prepare_graph(map_graph)
            if clean_graph is not None:
                tasks.append(OptimizationTask(
                    name="coordinator",
                    label="🌐 Tuning Coordinator (GATv2)",
                    objective_fn=lambda t, g=clean_graph: FlowStrategies.coordinator_strategy(t, g, device),
                    slope_threshold=1e-3
                ))

        # ═══════════════════════════════════════════════════════════════
        # Phase 2: Temporal — Fuser (iTransformer)
        # ═══════════════════════════════════════════════════════════════
        tasks.append(OptimizationTask(
            name="fuser",
            label="🔮 Tuning Fuser (iTransformer)",
            objective_fn=lambda t: FlowStrategies.fuser_strategy(t, univ_data, device)
        ))

        # ═══════════════════════════════════════════════════════════════
        # Phase 3: Local Patterns — Specialist (TCN)
        # ═══════════════════════════════════════════════════════════════
        tasks.append(OptimizationTask(
            name="specialist",
            label="🎯 Tuning Specialist (TCN)",
            objective_fn=lambda t: FlowStrategies.specialist_strategy(t, univ_data, device)
        ))

        # ═══════════════════════════════════════════════════════════════
        # Phase 4: Security — Auditor (Wavelet AE + OCC)
        # ═══════════════════════════════════════════════════════════════
        tasks.append(OptimizationTask(
            name="auditor",
            label="🛡️ Tuning Auditor (Wavelet AE + OCC)",
            objective_fn=lambda t: QualityStrategies.auditor_strategy(t, univ_data, device)
        ))

        # ═══════════════════════════════════════════════════════════════
        # Phase 5: Resilience — Imputer (PatchTST)
        # ═══════════════════════════════════════════════════════════════
        tasks.append(OptimizationTask(
            name="imputer",
            label="🧬 Tuning Imputer (PatchTST)",
            objective_fn=lambda t: QualityStrategies.imputer_strategy(t, univ_data, device),
            slope_threshold=1e-6,
            window=30
        ))

        # ═══════════════════════════════════════════════════════════════
        # Phase 6: Quality — Corrector (VAE-TCN)
        # ═══════════════════════════════════════════════════════════════
        tasks.append(OptimizationTask(
            name="corrector",
            label="🧹 Tuning Corrector (VAE-TCN)",
            objective_fn=lambda t: QualityStrategies.corrector_strategy(t, univ_data, device)
        ))

        # ═══════════════════════════════════════════════════════════════
        # Phase 7: Semantics — Linguist (TCN-AE Reasoner)
        # ═══════════════════════════════════════════════════════════════
        linguist_embeddings = TaskRegistry._prepare_linguist_embeddings(univ_data, device)
        tasks.append(OptimizationTask(
            name="linguist",
            label="🗣️ Tuning Linguist (TCN-AE)",
            objective_fn=lambda t, emb=linguist_embeddings: SemanticStrategies.linguist_strategy(t, emb, device)
        ))

        # ═══════════════════════════════════════════════════════════════
        # Phase 8: Classification — Peak Classifier (TimesNet)
        # ═══════════════════════════════════════════════════════════════
        inputs, targets = TaskRegistry._prepare_classifier_data(univ_data)
        if inputs is not None:
            tasks.append(OptimizationTask(
                name="classifier",
                label="📊 Tuning Peak Classifier (TimesNet)",
                objective_fn=lambda t, inp=inputs, tgt=targets: SemanticStrategies.classifier_strategy(t, inp, tgt, device)
            ))

        return tasks

    # ═══════════════════════════════════════════════════════════════════
    # PRIVATE: Data Preparation Helpers
    # ═══════════════════════════════════════════════════════════════════

    @staticmethod
    def _prepare_graph(map_graph: Any) -> Optional[Any]:
        """Converts map dict to PyG Data if needed."""
        if isinstance(map_graph, dict):
            if Data is not None:
                try:
                    logger.info("[TaskRegistry] 🛠️ Converting Map Dict → PyTorch Geometric Data...")
                    return Data(**map_graph)
                except Exception as e:
                    logger.warning(f"[TaskRegistry] ⚠️ Failed to convert map_graph: {e}")
                    return None
            else:
                logger.warning("[TaskRegistry] ⚠️ PyTorch Geometric not found. Skipping Coordinator.")
                return None
        return map_graph

    @staticmethod
    def _prepare_classifier_data(univ_data: np.ndarray):
        """
        Prepares sliding windows and binary labels for the Peak Classifier.
        
        Previously this logic lived inside optimizer_service.run() — violating SRP.
        """
        seq_len = 96
        sample_limit = 64

        if isinstance(univ_data, np.ndarray):
            series_1d = np.mean(univ_data, axis=1) if univ_data.ndim > 1 else univ_data
        else:
            series_1d = np.array(univ_data).flatten()

        threshold = np.mean(series_1d) + np.std(series_1d)

        needed_length = seq_len + sample_limit
        if len(series_1d) > needed_length:
            series_1d = series_1d[-needed_length:]

        x_windows = []
        y_labels = []

        for i in range(len(series_1d) - seq_len):
            window = series_1d[i: i + seq_len]
            target_val = series_1d[i + seq_len]
            x_windows.append(window)
            y_labels.append(1.0 if target_val > threshold else 0.0)

        if not x_windows:
            x_windows = [np.random.randn(seq_len)]
            y_labels = [1.0]

        inputs = np.array(x_windows, dtype=np.float32)
        targets = np.array(y_labels, dtype=np.float32)

        # Ensure at least one positive class to prevent BCE loss collapse
        if targets.sum() == 0:
            targets[0] = 1.0

        return inputs, targets

    @staticmethod
    def _prepare_linguist_embeddings(univ_data: Any, device: torch.device) -> torch.Tensor:
        """
        Pre-computes semantic embeddings from ModernBERT ONCE before Optuna trials begin.
        Decouples ModernBERT from the Optuna trial loop so HPO runs purely on the TCN-AE.
        """
        try:
            from transformers import AutoTokenizer, AutoModel
            from src.utils.model_paths import get_modernbert_path

            model_path = get_modernbert_path()
            is_local = os.path.isdir(model_path)

            tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=is_local)
            transformer = AutoModel.from_pretrained(model_path, local_files_only=is_local).to(device)
            transformer.eval()

            sample_texts = [
                "Traffic sensor flow volume peak at main intersection corridor.",
                "Normal operational vehicle speed telemetry stream.",
                "Congestion detected on arterial highway with decelerating speed.",
                "Free flow conditions observed across secondary collector avenue."
            ]
            tokens = tokenizer(
                sample_texts,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=64
            ).to(device)

            with torch.no_grad():
                outputs = transformer(**tokens)
                embeddings = outputs.last_hidden_state.permute(0, 2, 1).contiguous()

            del transformer
            del tokenizer
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            logger.info(f"[TaskRegistry] 🧠 Pre-computed Linguist embeddings once: shape {embeddings.shape}")
            return embeddings
        except Exception as e:
            logger.warning(f"[TaskRegistry] ⚠️ Transformer pre-compute skipped ({e}). Using synthetic calibration tensor.")
            return torch.randn(8, 768, 32, device=device)


