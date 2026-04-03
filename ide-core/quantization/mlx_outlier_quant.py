"""Non-integer bit precision via outlier channel splitting on MLX.

Translates turboquant_plus/outlier.py to native mlx.core.

For 3.5-bit: 50% channels at 4-bit + 50% at 3-bit = 3.5 avg
For 2.5-bit: 50% channels at 3-bit + 50% at 2-bit = 2.5 avg

Achieves better quality than uniform 3-bit by giving more bits to
high-variance "outlier" channels.
"""

import mlx.core as mx
import math

from quantization.mlx_polar_quant import MLXPolarQuant


def compute_channel_split(d: int, target_bits: float) -> tuple[int, int, int, int]:
    """Compute outlier vs normal channel split.

    Returns:
        (n_outlier, high_bits, n_normal, low_bits)
    """
    low_bits = int(math.floor(target_bits))
    high_bits = low_bits + 1
    frac = target_bits - low_bits
    n_outlier = int(round(d * frac))
    n_normal = d - n_outlier
    return n_outlier, high_bits, n_normal, low_bits


class MLXOutlierPolarQuant:
    """Non-integer bit-rate PolarQuant with outlier channel splitting.

    Usage:
        oq = MLXOutlierPolarQuant(d=128, target_bits=3.5, seed=42)
        compressed = oq.quantize(x)  # returns OutlierCompressed
        x_hat = oq.dequantize(compressed)
    """

    def __init__(self, d: int, target_bits: float, seed: int = 42, norm_correction: bool = True):
        self.d = d
        self.target_bits = target_bits

        n_outlier, high_bits, n_normal, low_bits = compute_channel_split(d, target_bits)
        self.n_outlier = n_outlier
        self.n_normal = n_normal
        self.high_bits = high_bits
        self.low_bits = low_bits
        self.effective_bits = (n_outlier * high_bits + n_normal * low_bits) / d

        # Separate quantizers for outlier and normal channel groups
        self.pq_outlier = (
            MLXPolarQuant(n_outlier, bit_width=high_bits, seed=seed, norm_correction=norm_correction)
            if n_outlier > 0 else None
        )
        self.pq_normal = (
            MLXPolarQuant(n_normal, bit_width=low_bits, seed=seed + 500, norm_correction=norm_correction)
            if n_normal > 0 else None
        )

    def quantize(self, x: mx.array) -> dict:
        """Quantize with outlier channel split.

        Args:
            x: Shape (d,) or (batch, d).

        Returns:
            Dict with outlier_indices, outlier_norms, normal_indices, normal_norms.
        """
        single = x.ndim == 1
        if single:
            x = x[None, :]

        # Split channels
        x_outlier = x[:, :self.n_outlier]
        x_normal = x[:, self.n_outlier:]

        result = {}

        if self.pq_outlier is not None:
            out_idx, out_nrm = self.pq_outlier.quantize(x_outlier)
            result["outlier_indices"] = out_idx
            result["outlier_norms"] = out_nrm
        else:
            result["outlier_indices"] = None
            result["outlier_norms"] = None

        if self.pq_normal is not None:
            nrm_idx, nrm_nrm = self.pq_normal.quantize(x_normal)
            result["normal_indices"] = nrm_idx
            result["normal_norms"] = nrm_nrm
        else:
            result["normal_indices"] = None
            result["normal_norms"] = None

        result["single"] = single
        return result

    def dequantize(self, compressed: dict) -> mx.array:
        """Dequantize outlier-split compressed vector."""
        parts = []

        if self.pq_outlier is not None and compressed["outlier_indices"] is not None:
            x_outlier = self.pq_outlier.dequantize(
                compressed["outlier_indices"], compressed["outlier_norms"]
            )
            parts.append(x_outlier)
        else:
            single = compressed.get("single", False)
            shape = (self.n_outlier,) if single else (compressed["normal_indices"].shape[0], self.n_outlier)
            parts.append(mx.zeros(shape))

        if self.pq_normal is not None and compressed["normal_indices"] is not None:
            x_normal = self.pq_normal.dequantize(
                compressed["normal_indices"], compressed["normal_norms"]
            )
            parts.append(x_normal)
        else:
            single = compressed.get("single", False)
            shape = (self.n_normal,) if single else (compressed["outlier_indices"].shape[0], self.n_normal)
            parts.append(mx.zeros(shape))

        x_hat = mx.concatenate(parts, axis=-1)

        if compressed.get("single", False):
            return x_hat[0] if x_hat.ndim > 1 else x_hat
        return x_hat

    def compression_ratio(self, original_bits: int = 16) -> float:
        per_vector_bits = self.d * self.effective_bits + 64  # 2 x 32-bit norms
        return (self.d * original_bits) / per_vector_bits
