# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
import pandas as pd
from typing import Dict, Any

from src.stages.base_stage import BaseStage
from src.agents.peak_classifier_agent import PeakClassifierAgent

class ClassificationStage(BaseStage):
    """
    Classification Stage (Step 4).
    
    Responsible solely for:
    - Checking if the peak schedule JSON already exists (Warm Start).
    - Loading the golden dataset.
    - Dynamically configuring the sequence length for the neural networks.
    - Initializing the PeakClassifierAgent (which now handles Semantic Discovery internally).
    - Executing the pipeline to generate peak_schedule.json.
    """

    def execute(self, shared_context: Dict[str, Any]) -> bool:
        """Executes the peak classification pipeline."""
        golden_path = shared_context.get("golden_path")
        json_path = shared_context.get("json_path")
        
        # Check if we can intelligently skip this phase (Warm Start)
        json_valid = os.path.exists(json_path) and os.path.getsize(json_path) > 0
        
        if json_valid:
            self.log("[ClassificationStage] ⚡ Warm Start: Peak schedule JSON found and valid. Skipping TimesNet Classifier.")
            self.progress(100)
            return True

        if self.check_interruption(): 
            return False

        self.log("[ClassificationStage] 📈 Step 4/4: Running Peak Classifier Agent (Semantic Discovery + TimesNet + iTransformer)...")
        
        try:
            # Load the validated Golden Dataset
            golden_df = pd.read_parquet(golden_path)
            
            # Dynamic sequence length based on the dataset size
            seq_len = len(golden_df)
            
            # Load Phase Zero Hyperparameters if available
            clf_cfg: Dict[str, Any] = {}
            hparams_candidates = [
                os.path.join(self.synapse_root, "Checkpoint", "best_hparams.pth"),
                os.path.join("checkpoints", "best_hparams.pth"),
            ]
            for hp_path in hparams_candidates:
                if os.path.exists(hp_path):
                    try:
                        import torch
                        hp_all = torch.load(hp_path, map_location="cpu")
                        if isinstance(hp_all, dict) and isinstance(hp_all.get("classifier"), dict):
                            clf_cfg = hp_all["classifier"]
                        break
                    except Exception:
                        pass

            d_model_val = int(clf_cfg.get("d_model", 64))
            top_k_val = int(clf_cfg.get("top_k", 3))
            lr_val = float(clf_cfg.get("lr", 1e-3))

            # Define Neural Network Configurations for ADAGIO Phase 1
            itrans_cfg = {
                'num_variates': 2, 
                'seq_len': seq_len, 
                'pred_len': seq_len, 
                'd_model': d_model_val
            }
            tnet_cfg = {
                'enc_in': 1, 
                'seq_len': seq_len, 
                'pred_len': seq_len, 
                'd_model': d_model_val,
                'top_k': top_k_val,
                'learning_rate': lr_val
            }
            
            # Initialize and execute the updated Peak Classifier Agent
            peak_classifier = PeakClassifierAgent(
                itransformer_config=itrans_cfg, 
                timesnet_config=tnet_cfg,
                output_path=json_path
            )
            
            peak_classifier.process_and_classify(golden_df)
            self.log("[ClassificationStage] 🕒 Peak schedule JSON generated successfully.")
            
        except Exception as e:
            self.log(f"[ClassificationStage] ❌ Error during classification: {str(e)}")
            return False
            
        self.progress(100)
        return True
