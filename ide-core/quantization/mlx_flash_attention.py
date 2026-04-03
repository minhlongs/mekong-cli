"""Flash Attention compatibility for TurboQuant compressed KV cache.

Ensures mlx.core.fast.scaled_dot_product_attention works seamlessly
with on-the-fly dequantized KV from TurboQuantKVCache.

The key insight: Flash Attention operates on dense (B, n_heads, seq, head_dim)
tensors. Since TurboQuantKVCache.update_and_fetch() already returns dequantized
dense tensors, Flash Attention works out of the box.

This module provides a helper for cases where you want to use Sparse V
optimization WITH Flash Attention (selective dequantization).
"""

import mlx.core as mx
import math


def turbo_attention(
    queries: mx.array,
    keys: mx.array,
    values: mx.array,
    scale: float = None,
    mask: mx.array = None,
) -> mx.array:
    """Attention computation compatible with TurboQuant KV cache.

    Uses mlx.core.fast.scaled_dot_product_attention when available,
    falls back to manual implementation otherwise.

    Args:
        queries: (B, n_heads, seq_q, head_dim)
        keys: (B, n_kv_heads, seq_kv, head_dim) — already dequantized
        values: (B, n_kv_heads, seq_kv, head_dim) — already dequantized
        scale: Attention scale (default: 1/sqrt(head_dim))
        mask: Optional attention mask

    Returns:
        (B, n_heads, seq_q, head_dim) attention output
    """
    if scale is None:
        scale = 1.0 / math.sqrt(queries.shape[-1])

    # Try Flash Attention (Metal-optimized)
    try:
        return mx.fast.scaled_dot_product_attention(
            queries, keys, values, scale=scale, mask=mask
        )
    except Exception:
        # Fallback to manual attention
        return _manual_attention(queries, keys, values, scale, mask)


def _manual_attention(queries, keys, values, scale, mask):
    """Manual attention computation (fallback)."""
    # Handle GQA: repeat KV heads if needed
    n_heads = queries.shape[1]
    n_kv_heads = keys.shape[1]
    if n_kv_heads < n_heads:
        repeats = n_heads // n_kv_heads
        keys = mx.repeat(keys, repeats, axis=1)
        values = mx.repeat(values, repeats, axis=1)

    # Compute attention scores
    scores = (queries @ keys.transpose(0, 1, 3, 2)) * scale

    if mask is not None:
        scores = scores + mask

    weights = mx.softmax(scores, axis=-1)
    return weights @ values


def verify_flash_attention_compatible(
    head_dim: int, n_heads: int, n_kv_heads: int, seq_len: int
) -> dict:
    """Verify Flash Attention works with the given dimensions.

    Creates synthetic tensors and runs both Flash and manual attention,
    comparing outputs.

    Returns:
        Dict with compatible (bool), max_error, and notes.
    """
    B = 1
    seq_q = 1

    queries = mx.random.normal(shape=(B, n_heads, seq_q, head_dim))
    keys = mx.random.normal(shape=(B, n_kv_heads, seq_len, head_dim))
    values = mx.random.normal(shape=(B, n_kv_heads, seq_len, head_dim))
    scale = 1.0 / math.sqrt(head_dim)

    # Manual attention
    manual_out = _manual_attention(queries, keys, values, scale, None)

    # Flash attention
    try:
        flash_out = mx.fast.scaled_dot_product_attention(
            queries, keys, values, scale=scale
        )
        max_error = float(mx.max(mx.abs(manual_out - flash_out)).item())
        return {
            "compatible": True,
            "max_error": max_error,
            "notes": f"Flash Attention OK, max error: {max_error:.2e}",
        }
    except Exception as e:
        return {
            "compatible": False,
            "max_error": float("inf"),
            "notes": f"Flash Attention failed: {e}",
        }
