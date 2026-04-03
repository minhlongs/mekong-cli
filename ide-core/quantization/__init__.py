"""MLX-native TurboQuant KV cache compression for Mekong IDE.

Extracted from turboquant_plus (ICLR 2026 paper: arXiv 2504.19874),
translated to pure mlx.core for Apple Silicon Metal acceleration.

Components:
- mlx_wht: Fast Walsh-Hadamard Transform + random sign flips
- mlx_polar_quant: PolarQuant scalar quantization with norm correction
- mlx_kv_cache: Unified KVCache with Boundary V strategy
- mlx_sparse_v: Sparse V attention optimization
"""

from quantization.mlx_wht import fast_wht, apply_rotation, apply_rotation_transpose
from quantization.mlx_polar_quant import MLXPolarQuant
from quantization.mlx_kv_cache import TurboKVCache
