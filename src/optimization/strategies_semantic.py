# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import torch
import torch.nn as nn
import numpy as np
from typing import Any
import logging
import optuna

# Import Models & Agents - Strict Encapsulation
from src.models.neuro_symbolic import TCNAE
from src.physics.traffic_loss import TrafficPhysicsLoss
from src.agents.peak_classifier_agent import PeakClassifierAgent
from src.utils.convergence_tracker import MarginalConvergenceTracker

logger = logging.getLogger("Synapse.Strategies.Semantic")

class SemanticStrategies:
    """
    Optimization Strategies for Semantic Agents (Language & Classification).
    
    Contains:
    1. Linguist Strategy (NLP / Neuro-Symbolic TCN-AE Reasoner)
    2. Classifier Strategy (Peak Detection via encapsulated TimesNet Agent)
    """

    @staticmethod
    def linguist_strategy(trial, data: Any, device: torch.device) -> float:
        """
        Optimizes the Linguist Reasoner (TCN-AE + PINN).
        Operates purely on semantic embeddings extracted from ModernBERT.
        Decoupled from the frozen Transformer to achieve sub-second trial times.
        """
        # 1. Hyperparameters for the TCN-AE
        lr = trial.suggest_float("lr", 1e-4, 1e-2, log=True)
        latent_dim = trial.suggest_categorical("latent_dim", [32, 64, 128])
        kernel_size = trial.suggest_categorical("kernel_size", [3, 5])
        
        # 2. Data Preparation: Ensure [Batch, HiddenSize, SeqLen] tensor
        if torch.is_tensor(data) and data.dim() == 3:
            embeddings = data.to(device)
        elif isinstance(data, np.ndarray) and data.ndim == 3:
            embeddings = torch.tensor(data, dtype=torch.float32, device=device)
        else:
            # Fallback for synthetic/legacy data
            embeddings = torch.randn(8, 768, 32, device=device)
            
        hidden_size = embeddings.shape[1]

        # 3. Instantiate pure TCN-AE (Zero Transformer overhead during HPO)
        try:
            tcn = TCNAE(
                hidden_size=hidden_size,
                latent_dim=latent_dim,
                kernel_size=kernel_size
            ).to(device)
            optimizer = torch.optim.Adam(tcn.parameters(), lr=lr)
            criterion = nn.MSELoss()
            physics_engine = TrafficPhysicsLoss(max_acceleration=10.0)
        except Exception as e:
            logger.error(f"[Linguist] TCN Init Error: {e}")
            return float('inf')

        # 4. Fast Dynamic Training Loop (Marginal Convergence + Pruning)
        try:
            tracker = MarginalConvergenceTracker(
                min_epochs=3,
                max_epochs=20,
                patience=3,
                min_delta=1e-4,
                optuna_trial=trial
            )
            
            for epoch in range(tracker.max_epochs):
                optimizer.zero_grad()
                reconstruction, latent, physics_states = tcn(embeddings)
                
                loss_recon = criterion(reconstruction, embeddings)
                physics_residuals = physics_engine.compute_losses(physics_states)
                loss_physics = physics_residuals.get("total_physics_loss", torch.tensor(0.0, device=device))
                total_loss = loss_recon + 0.1 * loss_physics
                
                if not torch.isfinite(total_loss):
                    return float('inf')
                    
                total_loss.backward()
                torch.nn.utils.clip_grad_norm_(tcn.parameters(), max_norm=1.0)
                optimizer.step()
                
                loss_val = total_loss.item()
                if tracker.step(epoch, loss_val, model=tcn):
                    break
            
            return tracker.best_loss
            
        except optuna.TrialPruned:
            raise
        except Exception as e:
            logger.warning(f"[Linguist] Training failed: {e}")
            return float('inf')
        finally:
            del tcn
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    @staticmethod
    def classifier_strategy(trial, inputs: np.ndarray, targets: np.ndarray, device: torch.device) -> float:
        """
        Optimizes the Peak Classifier Agent.
        Delegates model instantiation, loss calculation, and optimization entirely to the Agent.
        """
        # 1. Hyperparameters customized for Edge Hardware constraints (VRAM Limit: ~6GB)
        # REDUCED search space to prevent CUDA Out of Memory issues
        d_model = trial.suggest_categorical("d_model", [16, 32, 64]) # Reduced from [32, 64, 128]
        e_layers = trial.suggest_int("e_layers", 1, 2)               # Reduced from 1-3
        top_k = trial.suggest_int("top_k", 1, 3)                     # Reduced from 1-5
        lr = trial.suggest_float("lr", 1e-5, 1e-2, log=True)
        
        # 2. Input Validation
        if inputs is None or len(inputs) == 0:
            return float('inf')
            
        # 3. Instantiate Agent (The agent handles its internal TimesNet creation)
        try:
            itransformer_config = {
                'num_variates': 2,
                'seq_len': 96,
                'pred_len': 96,
                'e_layers': e_layers,
                'd_model': d_model,
                'learning_rate': lr
            }
            timesnet_config = {
                'enc_in': 1,
                'seq_len': 96,
                'pred_len': 96,
                'e_layers': e_layers,
                'd_model': d_model,
                'd_ff': d_model * 4,
                'top_k': top_k,
                'learning_rate': lr
            }
            
            agent = PeakClassifierAgent(
                itransformer_config=itransformer_config,
                timesnet_config=timesnet_config
            )
        except Exception as e:
            logger.error(f"[Classifier] Init Error: {e}")
            return float('inf')

        # 4. Dynamic Training Loop delegated to the Agent
        try:
            tracker = MarginalConvergenceTracker(
                min_epochs=3,
                max_epochs=20,
                patience=3,
                min_delta=1e-4,
                optuna_trial=trial
            )
            
            for epoch in range(tracker.max_epochs):
                # Agent internally handles AMP context, tensors mapping, and optimizer steps
                loss = agent.train_step(inputs, targets)
                if not np.isfinite(loss):
                    return float('inf')
                if tracker.step(epoch, loss):
                    break
            
            return tracker.best_loss

        except optuna.TrialPruned:
            raise
        except Exception as e:
            logger.warning(f"[Classifier] Training loop error: {e}")
            return float('inf')
        finally:
            del agent
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
