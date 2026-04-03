"""PolarQuant on MLX — Random rotation + optimal scalar quantization.

Translates turboquant_plus/polar_quant.py + codebook.py to native mlx.core.

Key adaptations:
- Codebook centroids precomputed at init (no scipy dependency at runtime)
- Lloyd's algorithm runs once in NumPy at init, then stored as mx.array
- Nearest centroid via MLX broadcast argmin (no searchsorted needed)
"""

import mlx.core as mx
import math
import numpy as np

from quantization.mlx_wht import generate_rotation_params, apply_rotation, apply_rotation_transpose


def _precompute_centroids(bit_width: int, d: int) -> mx.array:
    """Compute optimal centroids for post-rotation coordinate distribution.

    For 1-bit and 2-bit, uses closed-form from the TurboQuant paper.
    For higher bits, uses Lloyd's algorithm on N(0, 1/d).
    Runs in NumPy (one-time init cost), returns MLX array.
    """
    if bit_width == 1:
        c = math.sqrt(2.0 / (math.pi * d))
        return mx.array([-c, c])

    if bit_width == 2:
        scale = 1.0 / math.sqrt(d)
        return mx.array([-1.51 * scale, -0.453 * scale, 0.453 * scale, 1.51 * scale])

    # Lloyd's algorithm on N(0, sigma^2) where sigma = 1/sqrt(d)
    sigma = 1.0 / math.sqrt(d)
    n_centroids = 1 << bit_width
    centroids = _lloyds_gaussian_np(n_centroids, sigma)
    return mx.array(centroids)


def _lloyds_gaussian_np(n_centroids: int, sigma: float, n_iter: int = 100) -> np.ndarray:
    """Lloyd's algorithm in NumPy. One-time init cost."""
    from scipy import stats

    boundaries = stats.norm.ppf(
        np.linspace(0, 1, n_centroids + 1)[1:-1], scale=sigma
    )
    centroids = np.zeros(n_centroids)

    def cond_exp(a, b):
        a_std = a / sigma if np.isfinite(a) else a
        b_std = b / sigma if np.isfinite(b) else b
        if not np.isfinite(a_std):
            prob = stats.norm.cdf(b_std)
        elif not np.isfinite(b_std):
            prob = stats.norm.sf(a_std)
        else:
            prob = stats.norm.cdf(b_std) - stats.norm.cdf(a_std)
        if prob < 1e-15:
            if np.isfinite(a) and not np.isfinite(b):
                return a + sigma
            elif not np.isfinite(a) and np.isfinite(b):
                return b - sigma
            return (a + b) / 2.0 if np.isfinite(a) and np.isfinite(b) else 0.0
        return sigma * (stats.norm.pdf(a_std) - stats.norm.pdf(b_std)) / prob

    centroids[0] = cond_exp(-np.inf, boundaries[0])
    for i in range(1, n_centroids - 1):
        centroids[i] = cond_exp(boundaries[i - 1], boundaries[i])
    centroids[-1] = cond_exp(boundaries[-1], np.inf)

    for _ in range(n_iter):
        boundaries = (centroids[:-1] + centroids[1:]) / 2.0
        centroids[0] = cond_exp(-np.inf, boundaries[0])
        for i in range(1, n_centroids - 1):
            centroids[i] = cond_exp(boundaries[i - 1], boundaries[i])
        centroids[-1] = cond_exp(boundaries[-1], np.inf)

    return np.sort(centroids)


def _nearest_centroid_indices(values: mx.array, centroids: mx.array) -> mx.array:
    """Find nearest centroid for each value. Fully vectorized MLX.

    Uses broadcast: |values[..., None] - centroids[None, :]| → argmin over last axis.
    """
    # Compute boundaries (midpoints) for searchsorted-like behavior
    boundaries = (centroids[:-1] + centroids[1:]) / 2.0
    # Broadcast comparison: values > boundaries → sum gives insertion index
    # Shape: values (...) vs boundaries (k-1,) → (..., k-1) → sum axis=-1
    expanded = values[..., None]  # (..., 1)
    indices = mx.sum(expanded > boundaries[None, :], axis=-1)
    return indices


class MLXPolarQuant:
    """PolarQuant on MLX with norm correction.

    Usage:
        pq = MLXPolarQuant(d=128, bit_width=3, seed=42)
        indices, norms = pq.quantize(x)    # x: mx.array (d,) or (batch, d)
        x_hat = pq.dequantize(indices, norms)
    """

    def __init__(self, d: int, bit_width: int, seed: int = 42, norm_correction: bool = True):
        self.d = d
        self.bit_width = bit_width
        self.norm_correction = norm_correction

        # Structured rotation (WHT + signs)
        self.signs1, self.signs2, self.padded_d = generate_rotation_params(d, seed)

        # Precomputed codebook
        self.centroids = _precompute_centroids(bit_width, d)

    def quantize(self, x: mx.array) -> tuple[mx.array, mx.array]:
        """Quantize vector(s).

        Args:
            x: Shape (d,) or (batch, d).

        Returns:
            (indices, norms): indices are int32, norms are float32.
        """
        single = x.ndim == 1
        if single:
            x = x[None, :]

        # Extract norms and normalize
        norms = mx.linalg.norm(x, axis=1)
        safe_norms = mx.where(norms > 0, norms, mx.array(1.0))
        x_normalized = x / safe_norms[:, None]

        # Rotate
        y = apply_rotation(x_normalized, self.signs1, self.signs2, self.padded_d)

        # Nearest centroid
        indices = _nearest_centroid_indices(y, self.centroids)

        if single:
            return indices[0], norms[0]
        return indices, norms

    def dequantize(self, indices: mx.array, norms: mx.array) -> mx.array:
        """Dequantize indices back to vectors.

        Args:
            indices: Int32, shape (d,) or (batch, d).
            norms: Float32, scalar or (batch,).

        Returns:
            Reconstructed vectors.
        """
        single = indices.ndim == 1
        if single:
            indices = indices[None, :]
            norms = norms[None]

        # Lookup centroids
        y_hat = self.centroids[indices]

        # Norm correction: re-normalize reconstructed rotated vector to unit norm
        if self.norm_correction:
            y_norms = mx.linalg.norm(y_hat, axis=1, keepdims=True)
            y_norms = mx.where(y_norms > 1e-10, y_norms, mx.array(1.0))
            y_hat = y_hat / y_norms

        # Inverse rotation
        x_hat_unit = apply_rotation_transpose(y_hat, self.signs1, self.signs2, self.padded_d)

        # Rescale by original norms
        x_hat = x_hat_unit * norms[:, None]

        return x_hat[0] if single else x_hat

    def quantize_and_residual(self, x: mx.array) -> tuple[mx.array, mx.array, mx.array]:
        """Quantize and return residual for TurboQuant stage 2."""
        indices, norms = self.quantize(x)
        x_hat = self.dequantize(indices, norms)
        residual = x - x_hat
        return indices, norms, residual
