# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
import torch
import logging
from typing import Dict, Any, List

# --- Phase 2 (Online) Agent Imports ---
# Only importing agents strictly defined for the Runtime Phase.
from src.agents.coordinator_agent import CoordinatorAgent # GATv2 Lite
from src.agents.fuser_agent import FuserAgent             # iTransformer
from src.agents.auditor_agent import AuditorAgent         # Wavelet + AE + OCC
from src.agents.linguist_agent import LinguistAgent       # Neuro-symbolic (ModernBERT + TCN-AE)
from src.agents.jurist_agent import JuristAgent           # Qwen 2.5 1.5B
from src.agents.specialist_agent import SpecialistAgent   # TCN (The Analyst)

from src.engine.calibration.auditor_checkpoint_loader import AuditorCheckpointLoader


class NeuralFactory:
    """
    Factory class responsible for instantiating Neural Agents for PHASE 2 (Online).
    
    Adheres strictly to SOLID (SRP & DIP):
    - Instantiates and wires runtime neural agents.
    - Delegates checkpoint loading and calibration restoration to AuditorCheckpointLoader.
    """

    def __init__(self, weights_dir: str = "checkpoints/"):
        self.logger = logging.getLogger(__name__)
        self.weights_dir = weights_dir
        self.device = self._setup_device()
        self.checkpoint_loader = AuditorCheckpointLoader(weights_dir=self.weights_dir)
        self.agents: Dict[str, Any] = {}

    def _setup_device(self) -> torch.device:
        """
        Detects the best available hardware accelerator.
        """
        if torch.cuda.is_available():
            self.logger.info(f"Neural Factory: CUDA detected. Using {torch.cuda.get_device_name(0)}")
            # Enable Tensor Cores (TF32) globally for maximum throughput on Ampere+ GPUs
            torch.set_float32_matmul_precision('high')
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True
            return torch.device("cuda")
        elif torch.backends.mps.is_available():
            self.logger.info("Neural Factory: Apple MPS detected.")
            return torch.device("mps")
        else:
            self.logger.warning("Neural Factory: No accelerator detected. Using CPU.")
            return torch.device("cpu")

    def _load_best_hparams(self) -> Dict[str, Any]:
        """
        Loads the best hyperparameters found by Optuna (Phase Zero).
        """
        candidate_paths = [
            os.path.join(self.weights_dir, "best_hparams.pth"),
        ]
        env_dir = os.environ.get("SYNAPSE_CHECKPOINTS_DIR")
        if env_dir:
            candidate_paths.insert(0, os.path.join(env_dir, "best_hparams.pth"))

        from src.storage.path_scaffolder import PathScaffolder
        candidate_paths.extend([
            os.path.join("config", "best_hparams.pth"),
            PathScaffolder().get_checkpoint_file("best_hparams.pth"),
        ])
        
        for hparams_path in candidate_paths:
            if os.path.exists(hparams_path):
                try:
                    best_params = torch.load(hparams_path, map_location=torch.device('cpu'))
                    self.logger.info(f"Neural Factory: Loaded OPTIMIZED parameters from {hparams_path}")
                    return best_params
                except Exception as e:
                    self.logger.error(f"Neural Factory: Failed to load hparams file at {hparams_path}: {e}")
        
        self.logger.info("Neural Factory: Phase Zero file not found. Using Legacy Defaults.")
        return {}

    def build_all(self, app_state: Any) -> Dict[str, Any]:
        """
        Instantiates ONLY the agents required for Online Operation (Phase 2).
        """
        self.logger.info("Neural Factory: Starting Runtime Agent Ecosystem initialization...")
        
        # 1. Topology Analysis
        nodes = app_state.get_all_nodes()
        num_nodes = len(nodes) if nodes else 10
        self.logger.info(f"Neural Factory: Configuring agents for Topology Size: {num_nodes} nodes.")

        # 2. Load Dynamic Hyperparameters
        hparams = self._load_best_hparams()

        try:
            # === PHASE 2 AGENTS ===

            # 1. Specialist Agent (The Analyst - TCN)
            spec_cfg = hparams.get('specialist', {}) if isinstance(hparams.get('specialist'), dict) else {}
            spec_hidden = spec_cfg.get('hidden_dim', 64)
            default_spec_channels = [16, 32, int(spec_hidden)] if spec_hidden else [16, 32, 64]
            self.agents['specialist'] = SpecialistAgent(
                input_dim=4,  # [Occupancy, Speed, Queue, Density]
                output_dim=spec_cfg.get('output_dim', hparams.get('specialist_out', 16)),
                num_channels=spec_cfg.get('num_channels', hparams.get('specialist_channels', default_spec_channels)),
                kernel_size=spec_cfg.get('kernel_size', hparams.get('specialist_kernel', 3)),
                dropout=spec_cfg.get('dropout', hparams.get('specialist_dropout', 0.2))
            )

            # 2. Coordinator Agent (GATv2 Lite)
            coord_cfg = hparams.get('coordinator', {}) if isinstance(hparams.get('coordinator'), dict) else {}
            self.agents['coordinator'] = CoordinatorAgent(
                in_channels=32,   # FIX: TCN outputs 32-dim latent embedding, not 4-dim raw
                hidden_channels=coord_cfg.get('hidden_channels', hparams.get('coordinator_hidden', 32)),
                out_channels=coord_cfg.get('out_channels', hparams.get('coordinator_out', 32)),
                heads=coord_cfg.get('heads', hparams.get('coordinator_heads', 2)),
                dropout=coord_cfg.get('dropout', hparams.get('coordinator_dropout', 0.1))
            )

            # 3. Fuser Agent (iTransformer)
            fuser_cfg = hparams.get('fuser', {}) if isinstance(hparams.get('fuser'), dict) else {}
            fuser = FuserAgent(
                seq_len=fuser_cfg.get('seq_len', hparams.get('seq_len', 60)),
                pred_len=fuser_cfg.get('pred_len', hparams.get('pred_len', 12)),
                num_variates=num_nodes,
                d_model=fuser_cfg.get('d_model', hparams.get('fuser_d_model', 64)),
                n_heads=fuser_cfg.get('n_heads', hparams.get('fuser_n_heads', 4)),
                layers=fuser_cfg.get('layers', hparams.get('fuser_layers', 2)),
                learning_rate=fuser_cfg.get('lr', hparams.get('fuser_lr', 1e-4))
            )
            try:
                from src.mlops.mlops_pipe import create_mlops_pipe
                from src.mlops.mlops_process import MLOpsProcess
                mlops_pipe = create_mlops_pipe()
                mlops_process = MLOpsProcess(pipe=mlops_pipe)
                fuser.attach_mlops(pipe=mlops_pipe, process=mlops_process)
                mlops_process.start()
                self.logger.info("[NeuralFactory] 🚀 MLOps Out-of-Process Worker & Pipe attached to FuserAgent.")
            except Exception as e:
                self.logger.warning(f"[NeuralFactory] Could not initialize MLOpsProcess: {e}")
            self.agents['fuser'] = fuser

            # 4. Auditor Agent (Wavelet Scattering + AE + OCC)
            aud_cfg = hparams.get('auditor', {}) if isinstance(hparams.get('auditor'), dict) else {}
            aud_meta = self.checkpoint_loader.peek_checkpoint_meta()
            self.agents['auditor'] = AuditorAgent(
                input_len=aud_meta.get('input_len', aud_cfg.get('input_len', hparams.get('seq_len', 60))),
                J=aud_meta.get('J', aud_cfg.get('J', hparams.get('auditor_J', 2))),
                Q=aud_meta.get('Q', aud_cfg.get('Q', hparams.get('auditor_Q', 1))),
                latent_dim=aud_meta.get('latent_dim', aud_cfg.get('latent_dim', hparams.get('auditor_latent', 16))),
                learning_rate=aud_cfg.get('lr', hparams.get('auditor_lr', 1e-3))
            )
            
            # --- Load Offline Calibration (Cold-Start Elimination) ---
            self.checkpoint_loader.load_calibration(self.agents['auditor'])

            # 5. Linguist Agent (Neuro-Symbolic)
            ling_cfg = hparams.get('linguist', {}) if isinstance(hparams.get('linguist'), dict) else {}
            self.agents['linguist'] = LinguistAgent(
                latent_dim=ling_cfg.get('latent_dim', hparams.get('linguist_latent', 64)),
                kernel_size=ling_cfg.get('kernel_size', hparams.get('linguist_kernel', 3)),
                learning_rate=ling_cfg.get('lr', hparams.get('linguist_lr', 1e-4))
            )

            # 6. Jurist Agent (Qwen 3.5 GGUF)
            self.agents['jurist'] = JuristAgent()
            
            # --- Device Placement (CRITICAL FIX) ---
            for name, agent in self.agents.items():
                # Jurist manages its own device map (accelerate/bitsandbytes)
                if name == 'jurist': 
                    continue

                # FIX: Check if it's an nn.Module (BaseAgent inherits from it)
                # Calling .to() on the Agent updates 'self.device' AND moves the weights.
                if isinstance(agent, torch.nn.Module):
                    agent.to(self.device)
                
                # Fallback for agents that might wrap a model but not inherit properly
                else:
                    agent_model = getattr(agent, "model", None)
                    to_fn = getattr(agent_model, "to", None) if agent_model is not None else None
                    if callable(to_fn):
                        to_fn(self.device)

            # --- Selective In-Place Torch Inductor Compilation (Pure-PyTorch Backbones Only) ---
            from src.utils.hardware import maybe_compile_module
            spec_agent = self.agents.get("specialist")
            spec_model = getattr(spec_agent, "model", None) if spec_agent is not None else None
            if isinstance(spec_model, torch.nn.Module):
                maybe_compile_module(spec_model, device=self.device, dynamic=True)

            fuser_agent = self.agents.get("fuser")
            fuser_pipe = getattr(fuser_agent, "pipeline", None) if fuser_agent is not None else None
            fuser_mods = getattr(fuser_pipe, "module_dict", None) if fuser_pipe is not None else None
            if isinstance(fuser_mods, torch.nn.ModuleDict):
                for sub_name in ("itransformer", "pinn", "deeponet"):
                    if sub_name in fuser_mods and isinstance(fuser_mods[sub_name], torch.nn.Module):
                        maybe_compile_module(fuser_mods[sub_name], device=self.device, dynamic=True)
            
            self.logger.info(f"Neural Factory: Successfully initialized {len(self.agents)} Runtime Agents on {self.device}.")
            return self.agents

        except Exception as e:
            self.logger.critical(f"Neural Factory: Critical failure during Agent construction. {str(e)}")
            raise e

    def get_device(self) -> torch.device:
        return self.device

    def _get_auditor_checkpoint_candidates(self) -> List[str]:
        """Backward-compatibility shim delegating to AuditorCheckpointLoader."""
        return self.checkpoint_loader.get_checkpoint_candidates()

    def _peek_auditor_checkpoint_meta(self) -> Dict[str, Any]:
        """Backward-compatibility shim delegating to AuditorCheckpointLoader."""
        return self.checkpoint_loader.peek_checkpoint_meta()

    def _load_auditor_calibration(self, auditor: AuditorAgent):
        """Backward-compatibility shim delegating to AuditorCheckpointLoader."""
        return self.checkpoint_loader.load_calibration(auditor)
