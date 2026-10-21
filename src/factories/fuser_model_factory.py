# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import torch.nn as nn
from src.models.itransformer import iTransformer
from src.models.diffusion_gatv2 import DiffusionGATv2
from src.models.pino_traffic import PINOTrafficFlow1D
from src.models.pi_deeponet import PIDeepONet
from src.pipeline.fusion_pipeline import FusionPipeline


class FuserModelFactory:
    """
    Fabricator for the Fuser's neural components and pipelines (DIP/IoC).
    
    Adheres to Dependency Inversion Principle (DIP):
    - Decouples concrete PyTorch model construction from the FuserAgent orchestrator.
    - Encapsulates hyperparameter wiring across DiffusionGATv2, PINOTrafficFlow1D, PIDeepONet, and iTransformer.
    """

    @staticmethod
    def create_fusion_pipeline(
        num_variates: int = 10,
        seq_len: int = 60,
        pred_len: int = 1,
        d_model: int = 64,
        n_heads: int = 4,
        layers: int = 2,
        spatial_dim: int = 32,
        coord_dim: int = 2,
        p_latent: int = 64
    ) -> FusionPipeline:
        """
        Instantiates DiffusionGATv2, PINOTrafficFlow1D, PIDeepONet, and iTransformer and returns a configured FusionPipeline.
        """
        composite_dict = FuserModelFactory.create_composite_model(
            num_variates=num_variates,
            seq_len=seq_len,
            pred_len=pred_len,
            d_model=d_model,
            n_heads=n_heads,
            layers=layers,
            spatial_dim=spatial_dim,
            coord_dim=coord_dim,
            p_latent=p_latent
        )
        return FusionPipeline(
            diffusion_model=composite_dict["diffusion"],
            pinn_model=composite_dict["pinn"],
            temporal_model=composite_dict["itransformer"],
            deeponet_model=composite_dict["deeponet"],
            spatial_dim=spatial_dim
        )

    @staticmethod
    def create_composite_model(
        num_variates: int = 10,
        seq_len: int = 60,
        pred_len: int = 1,
        d_model: int = 64,
        n_heads: int = 4,
        layers: int = 2,
        spatial_dim: int = 32,
        coord_dim: int = 2,
        p_latent: int = 64
    ) -> nn.ModuleDict:
        """
        Creates the coupled neural architecture required by the Fuser pipeline.
        
        Returns:
            nn.ModuleDict with 'itransformer', 'diffusion', 'pinn', and 'deeponet' sub-modules.
        """
        effective_pred_len = 1

        # 1. Primary Inverted Transformer Model
        itrans_model = iTransformer(
            num_variates=num_variates,
            seq_len=seq_len,
            pred_len=effective_pred_len,
            d_model=d_model,
            n_heads=n_heads,
            e_layers=layers,
            spatial_dim=spatial_dim
        )

        # 2. Diffusion Graph WaveNet Model
        diffusion_model = DiffusionGATv2(
            num_nodes=num_variates,
            in_channels=spatial_dim,
            hidden_channels=64,
            out_channels=spatial_dim,
            diffusion_steps=2,
            gat_heads=2
        )

        # 3. Physics-Informed Neural Operator (PINO) Traffic Flow Model
        pinn_model = PINOTrafficFlow1D(
            in_channels=spatial_dim,
            hidden_dim=64
        )

        # 4. Physics-Informed Deep Operator Network (PI-DeepONet) Model
        deeponet_model = PIDeepONet(
            sensor_dim=num_variates,
            seq_len=seq_len,
            coord_dim=coord_dim,
            p_latent=p_latent,
            hidden_dim=128,
            out_channels=3  # [density, speed, flow]
        )

        return nn.ModuleDict({
            "itransformer": itrans_model,
            "diffusion": diffusion_model,
            "pinn": pinn_model,
            "deeponet": deeponet_model
        })
