# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import torch
import gc
import numpy as np
import logging
from typing import Optional, Callable
from torch.amp import autocast
from src.utils.hardware import get_optimal_amp_dtype

# Configure logger for this module
logger = logging.getLogger(__name__)

class BatchInferenceEngine:
    """
    Infrastructure Component.
    
    Responsibility: 
    - Execute ANY PyTorch model on ANY large dataset safely.
    - Encapsulates VRAM Management (CUDA Cache clearing).
    - Handles Data Slicing (Sliding Window) to prevent OOM errors.
    - Accelerates inference via Automatic Mixed Precision (AMP).
    
    Usage:
    engine = BatchInferenceEngine(device, batch_size=256)
    result = engine.run(model, raw_data, seq_len=24)
    """

    def __init__(self, device: torch.device, batch_size: int = 256, use_amp: bool = True):
        """
        Args:
            device: The target torch device (CPU/CUDA).
            batch_size: Number of windows to process at once. Decrease if OOM persists.
            use_amp: Whether to use Automatic Mixed Precision for Tensor Core acceleration.
        """
        self.device = device
        self.batch_size = batch_size
        self.use_amp = use_amp

    def run(self, 
            model: torch.nn.Module, 
            data_matrix: np.ndarray, 
            seq_len: int, 
            progress_callback: Optional[Callable[[int], None]] = None) -> np.ndarray:
        """
        Generic execution method for time-series reconstruction/inference.
        
        Args:
            model: The neural network (already loaded).
            data_matrix: The raw input numpy array (N samples, Features).
            seq_len: The sequence length the model expects (Sliding Window size).
            progress_callback: Optional function (accepts int 0-100) to report progress.
            
        Returns:
            np.ndarray: Reconstructed matrix aligned with input size (same N samples).
        """
        num_samples = len(data_matrix)
        
        # Validation
        if num_samples < seq_len:
            logger.warning(f"[BatchEngine] Data too short ({num_samples}) for seq_len {seq_len}.")
            return np.zeros_like(data_matrix)

        reconstructed_list = []
        device_type = self.device.type if self.device.type != 'mps' else 'cpu'
        amp_dtype = get_optimal_amp_dtype(self.device)
        use_cuda = (self.device.type == 'cuda')
        
        # Prepare Model
        model.eval()
        model.to(self.device)
        
        logger.info(f"[BatchEngine] Processing {num_samples} samples on {self.device} with batch_size {self.batch_size} (AMP={self.use_amp})...")

        # Zero-copy sliding window view: [num_windows, seq_len, features]
        all_windows = np.lib.stride_tricks.sliding_window_view(data_matrix, window_shape=seq_len, axis=0)
        if data_matrix.ndim == 2:
            all_windows = np.swapaxes(all_windows, 1, 2)
        total_windows = all_windows.shape[0]

        # Disable Gradient Calculation to save memory
        with torch.no_grad():
            # Main Loop: Slice data into vectorized mini-batches
            for i in range(0, total_windows, self.batch_size):
                batch_np = np.ascontiguousarray(all_windows[i : i + self.batch_size], dtype=np.float32)
                if batch_np.shape[0] == 0:
                    break
                
                # 2. Upload to GPU via pinned non-blocking DMA when on CUDA
                tensor_batch = torch.from_numpy(batch_np)
                if use_cuda:
                    tensor_batch = tensor_batch.pin_memory().to(self.device, non_blocking=True)
                else:
                    tensor_batch = tensor_batch.to(self.device)
                
                # 3. Inference with optimal AMP dtype (BF16 on Ampere+, FP16 on Turing)
                with autocast(device_type=device_type, dtype=amp_dtype, enabled=(self.use_amp and use_cuda)):
                    recon_batch = model(tensor_batch)
                
                # 4. Extract Strategy (Last Point)
                last_point_recon = recon_batch[:, -1, :]
                
                # 5. Download to CPU & Store
                reconstructed_list.append(last_point_recon.cpu().float().numpy())
                
                # 6. Immediate Cleanup
                del tensor_batch, recon_batch
                
                # 7. Periodic progress reporting (without per-batch blocking CUDA syncs)
                if i > 0 and i % 5120 == 0:
                    self._force_cleanup()
                    if progress_callback:
                        percent = int((i / num_samples) * 100)
                        progress_callback(percent)
                elif i == 0 and progress_callback:
                    progress_callback(0)

        # 8. Reassemble
        if not reconstructed_list:
            return np.zeros_like(data_matrix)

        reconstructed_matrix = np.concatenate(reconstructed_list, axis=0)
        
        # 9. Time Alignment (Padding)
        # Sliding window reduces output size by (seq_len - 1).
        # We assume the model "predicts" or "corrects" the end of the window.
        # So we pad the beginning with original data to match length.
        pad_width = num_samples - len(reconstructed_matrix)
        
        if pad_width > 0:
            padding = data_matrix[:pad_width]
            final_matrix = np.vstack([padding, reconstructed_matrix])
        else:
            final_matrix = reconstructed_matrix
            
        # Final cleanup before returning
        self._force_cleanup()
        
        return final_matrix

    def _force_cleanup(self):
        """
        Executes aggressive memory release protocols.
        """
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
