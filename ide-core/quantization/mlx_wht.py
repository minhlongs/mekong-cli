"""Fast Walsh-Hadamard Transform on MLX (Apple Silicon Metal).

Translates the O(d log d) structured random rotation from turboquant_plus/rotation.py
to native mlx.core tensors. Used as the rotation step in PolarQuant.

Key difference from NumPy: MLX uses lazy evaluation + Metal GPU, so butterfly ops
are fused into a single Metal kernel when possible.
"""

import mlx.core as mx
import math


def _next_power_of_2(n: int) -> int:
    p = 1
    while p < n:
        p <<= 1
    return p


def fast_wht(x: mx.array) -> mx.array:
    """Fast Walsh-Hadamard Transform on MLX. O(n log n).

    Args:
        x: Input array, shape (n,) or (batch, n). n must be power of 2.

    Returns:
        Transformed array, normalized by 1/sqrt(n).
    """
    if x.ndim == 1:
        return _fast_wht_1d(x)
    return _fast_wht_batch(x)


def _fast_wht_1d(x: mx.array) -> mx.array:
    n = x.shape[0]
    h = 1
    while h < n:
        # Butterfly: reshape to pairs, add/subtract
        x_reshaped = x.reshape(-1, 2, h)
        a = x_reshaped[:, 0, :]
        b = x_reshaped[:, 1, :]
        top = a + b
        bot = a - b
        x = mx.concatenate([top[:, None, :], bot[:, None, :]], axis=1).reshape(-1)
        h *= 2
    return x / math.sqrt(n)


def _fast_wht_batch(x: mx.array) -> mx.array:
    """Batched WHT: shape (batch, n)."""
    batch, n = x.shape
    h = 1
    while h < n:
        x_reshaped = x.reshape(batch, -1, 2, h)
        a = x_reshaped[:, :, 0, :]
        b = x_reshaped[:, :, 1, :]
        top = a + b
        bot = a - b
        x = mx.concatenate([top[:, :, None, :], bot[:, :, None, :]], axis=2).reshape(batch, n)
        h *= 2
    return x / math.sqrt(n)


def generate_rotation_params(d: int, seed: int = 42) -> tuple[mx.array, mx.array, int]:
    """Generate random sign vectors for structured rotation D2 @ H @ D1.

    Args:
        d: Original dimension.
        seed: Random seed.

    Returns:
        (signs1, signs2, padded_d)
    """
    padded_d = _next_power_of_2(d)
    key = mx.random.key(seed)
    k1, k2 = mx.random.split(key)
    signs1 = mx.where(mx.random.uniform(shape=(padded_d,), key=k1) < 0.5, -1.0, 1.0)
    signs2 = mx.where(mx.random.uniform(shape=(padded_d,), key=k2) < 0.5, -1.0, 1.0)
    return signs1, signs2, padded_d


def apply_rotation(x: mx.array, signs1: mx.array, signs2: mx.array, padded_d: int) -> mx.array:
    """Apply structured random rotation: D2 @ H @ D1 @ x.

    Args:
        x: Input, shape (d,) or (batch, d).
        signs1, signs2: Random sign vectors from generate_rotation_params.
        padded_d: Power-of-2 padded dimension.

    Returns:
        Rotated array, same leading shape, dimension d.
    """
    single = x.ndim == 1
    if single:
        x = x[None, :]

    batch, d = x.shape
    # Pad to power of 2
    if d < padded_d:
        padding = mx.zeros((batch, padded_d - d))
        x_padded = mx.concatenate([x, padding], axis=1)
    else:
        x_padded = x

    # D1 @ x
    x_padded = x_padded * signs1[None, :]
    # H @ D1 @ x
    x_padded = _fast_wht_batch(x_padded)
    # D2 @ H @ D1 @ x
    x_padded = x_padded * signs2[None, :]

    result = x_padded[:, :d]
    return result[0] if single else result


def apply_rotation_transpose(y: mx.array, signs1: mx.array, signs2: mx.array, padded_d: int) -> mx.array:
    """Apply transpose of structured rotation: D1 @ H @ D2 @ y.

    H and D are symmetric/self-inverse, so transpose reverses the order.
    """
    single = y.ndim == 1
    if single:
        y = y[None, :]

    batch, d = y.shape
    if d < padded_d:
        padding = mx.zeros((batch, padded_d - d))
        y_padded = mx.concatenate([y, padding], axis=1)
    else:
        y_padded = y

    # Reverse: D2 first, then H, then D1
    y_padded = y_padded * signs2[None, :]
    y_padded = _fast_wht_batch(y_padded)
    y_padded = y_padded * signs1[None, :]

    result = y_padded[:, :d]
    return result[0] if single else result
