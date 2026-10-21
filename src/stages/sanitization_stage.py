# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
import pandas as pd
import numpy as np
from typing import Dict, Any

from src.stages.base_stage import BaseStage
from src.agents.corrector_agent import CorrectorAgent
from src.agents.imputer_agent import ImputerAgent

class SanitizationStage(BaseStage):
    """
    Sanitization Stage (Step 0, 1, and 2).
    
    Responsible solely for:
    - Finding the raw input data.
    - Creating the base backup.
    - Running the CorrectorAgent (VAE-TCN) to remove outliers/noise.
    - Running the ImputerAgent (PatchTST) to fill temporal gaps.
    - Generating the optimized 'golden_v1.parquet' dataset.
    """

    def execute(self, shared_context: Dict[str, Any]) -> bool:
        """Executes the data cleaning and imputation pipeline."""
        golden_path = shared_context.get("golden_path")
        base_dir = shared_context.get("base_dir")
        
        # Check if we can intelligently skip this heavy phase
        golden_valid = os.path.exists(golden_path) and os.path.getsize(golden_path) > 0
        if golden_valid:
            self.log(f"[SanitizationStage] 🏆 Golden dataset validated: {golden_path}")
            self.log("[SanitizationStage] ⏩ Skipping sanitization (VAE-TCN and PatchTST).")
            self.progress(60)
            return True

        if self.check_interruption(): return False

        # Step 0: Locate Input Data (STRICT)
        input_file = self._find_input_parquet()
        if not input_file:
            self.log("[SanitizationStage] ❌ CRITICAL: No input .parquet file found in Synapse folder.")
            raise FileNotFoundError("No input .parquet file found. Please import a file first.")
        
        self.log(f"[SanitizationStage] 📂 Found Input: {os.path.basename(input_file)}")
        
        # Step 0.5: Load and Create Base Copy (Exact Duplicate)
        df_raw = pd.read_parquet(input_file)
        base_path = os.path.join(base_dir, "base_v1.parquet")
        df_raw.to_parquet(base_path) 
        
        self.log(f"[SanitizationStage] 💾 BASE Created (Exact Copy): {base_path}")
        self.log(f"[SanitizationStage] 📊 Input Shape: {df_raw.shape}")
        self.progress(25)

        if self.check_interruption(): return False

        # Step 1 & 2: Pipeline - Correction and Imputation (Isolated per Sensor)
        TARGET_COLS = ['speed_val', 'flow_val', 'intensity_val']
        
        # Ensure targeted columns exist
        available_cols = [c for c in TARGET_COLS if c in df_raw.columns]
        if not available_cols:
            self.log("[SanitizationStage] ⚠️ Target columns missing. Falling back to all non-spatial numerics.")
            numeric_cols = df_raw.select_dtypes(include=[np.number]).columns.tolist()
            excluded_cols = ['lat', 'lon', 'latitude', 'longitude']
            available_cols = [c for c in numeric_cols if c.lower() not in excluded_cols]
            if not available_cols:
                raise ValueError("Dataset has no valid numeric columns for processing.")

        df_golden = df_raw.copy()
        
        # Ensure targeted numeric columns are float64 so they can receive continuous float corrections and imputations
        for col in available_cols:
            df_golden[col] = pd.to_numeric(df_golden[col], errors='coerce').astype(np.float64)
        
        # Safety net for missing grouping key
        if 'sensor_id' not in df_raw.columns:
            self.log("[SanitizationStage] ⚠️ No 'sensor_id' found! Processing entire dataset as one continuous block.")
            df_golden['sensor_id'] = 'default_sensor'

        self.log(f"[SanitizationStage] 🧹 Initializing VAE-TCN and PatchTST agents for {len(available_cols)} features...")
        num_features = len(available_cols)

        corr_cfg: Dict[str, Any] = {}
        imp_cfg: Dict[str, Any] = {}
        hparams_candidates = [
            os.path.join(self.synapse_root, "Checkpoint", "best_hparams.pth"),
            os.path.join("checkpoints", "best_hparams.pth"),
        ]
        for hp_path in hparams_candidates:
            if os.path.exists(hp_path):
                try:
                    import torch
                    hp_all = torch.load(hp_path, map_location="cpu")
                    if isinstance(hp_all, dict):
                        if isinstance(hp_all.get("corrector"), dict):
                            corr_cfg = hp_all["corrector"]
                        if isinstance(hp_all.get("imputer"), dict):
                            imp_cfg = hp_all["imputer"]
                    break
                except Exception:
                    pass

        corrector_agent = CorrectorAgent(
            input_dim=num_features,
            latent_dim=int(corr_cfg.get("latent_dim", 16)),
            kernel_size=int(corr_cfg.get("kernel_size", 3)),
            learning_rate=float(corr_cfg.get("lr", 1e-3)),
        )
        imp_patch_len = int(imp_cfg.get("patch_len", 8))
        imputer_agent = ImputerAgent(
            feature_dim=num_features,
            seq_len=24,
            patch_len=imp_patch_len,
            stride=max(1, imp_patch_len // 2),
            d_model=int(imp_cfg.get("d_model", 64)),
            n_heads=int(imp_cfg.get("n_heads", 4)),
            n_layers=int(imp_cfg.get("n_layers", 2)),
            dropout=float(imp_cfg.get("dropout", 0.1)),
            learning_rate=float(imp_cfg.get("lr", 1e-4)),
        )

        groups = df_golden.groupby('sensor_id')
        total_gaps = 0

        for sensor, group_df in groups:
            if len(group_df) < 2:
                self.log(f"[SanitizationStage] ⚠️ Sensor '{sensor}' has only {len(group_df)} row! Ignoring to prevent statistical corruption.")
                continue

            data_matrix = group_df[available_cols].values.astype(np.float32)
            
            # Step 1: Correction (VAE-TCN) - Injects NaNs on outliers
            processed_matrix = self._apply_corrector(data_matrix, corrector_agent)
            
            # Step 2: Imputation (PatchTST) - Fills NaNs using temporal context
            nan_count = np.isnan(processed_matrix).sum()
            total_gaps += nan_count
            
            if nan_count > 0:
                self.log(f"[SanitizationStage] 🧬 Sensor '{sensor}': Found {nan_count} gaps/outliers. Imputing...")
                processed_matrix = self._apply_imputer(processed_matrix, imputer_agent)
                
            # Safely restore the processed window back into the main DataFrame
            df_golden.loc[group_df.index, available_cols] = processed_matrix

        self.progress(55)

        if self.check_interruption(): return False

        # Reassemble and Enrich
        if 'timestamp' in df_golden.columns or 'event_timestamp' in df_golden.columns:
            df_golden = self._enrich_time_features(df_golden)
            
        # Clean up fallback if needed
        if 'sensor_id' not in df_raw.columns:
            df_golden = df_golden.drop(columns=['sensor_id'])

        df_golden.to_parquet(golden_path)
        
        self.log(f"[SanitizationStage] 🏆 GOLDEN dataset generated: {golden_path} (Filled {total_gaps} gaps)")
        self.progress(60)
        
        return True

    def _find_input_parquet(self) -> str:
        """
        Searches for a .parquet file to use as source.
        Prioritizes files NOT in 'base' or 'golden' to avoid recursion.
        """
        candidates = []
        for root, _, files in os.walk(self.synapse_root):
            for file in files:
                if file.endswith(".parquet"):
                    full_path = os.path.join(root, file)
                    if "golden_v1.parquet" in file:
                        continue 
                    candidates.append(full_path)
        
        if not candidates:
            return None
            
        return max(candidates, key=os.path.getmtime)

    def _apply_corrector(self, data: np.ndarray, agent: CorrectorAgent) -> np.ndarray:
        """Uses CorrectorAgent to smooth data and inject NaNs on anomalies."""
        import warnings
        corrected = agent.inference(data)
        
        deviation = np.abs(data - corrected)
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            threshold = np.nanstd(data, axis=0) * 3  # 3 Sigma
        
        threshold = np.where(np.isnan(threshold) | (threshold == 0), 1e-6, threshold)
        
        mask = deviation > threshold
        output = data.copy()
        output[mask] = np.nan # Create hole for Imputer
        
        return output

    def _apply_imputer(self, data: np.ndarray, agent: ImputerAgent) -> np.ndarray:
        """Uses ImputerAgent to fill NaNs created by the Corrector."""
        return agent.impute(data)

    def _enrich_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extracts standard temporal markers needed for downstream analysis."""
        time_col = 'timestamp' if 'timestamp' in df.columns else 'event_timestamp'
        df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
        df['hour'] = df[time_col].dt.hour
        df['day_of_week'] = df[time_col].dt.dayofweek
        return df
