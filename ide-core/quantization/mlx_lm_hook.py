"""Drop-in TurboQuant KV Cache for mlx-lm.

Replaces mlx-lm's KVCache with TurboQuant compression.
Compatible with mlx-lm's `update_and_fetch(keys, values)` interface.

Usage:
    from quantization.mlx_lm_hook import make_turbo_prompt_cache, patch_model_cache

    # Option 1: Create cache directly
    cache = make_turbo_prompt_cache(model, bit_width=4, boundary_layers=2)

    # Option 2: Monkey-patch existing model
    patch_model_cache(model, bit_width=4, boundary_layers=2)
"""

import mlx.core as mx
from quantization.mlx_polar_quant import MLXPolarQuant


class TurboQuantKVCache:
    """Per-layer KV cache with TurboQuant compression.

    For boundary layers: stores full-precision keys/values (like standard KVCache).
    For middle layers: compresses with PolarQuant on update, dequantizes on fetch.

    Shape convention (mlx-lm standard):
        keys/values: (B, n_kv_heads, seq_len, head_dim)
    """
    step = 256

    def __init__(
        self,
        layer_idx: int,
        num_layers: int,
        bit_width: int = 4,
        boundary_layers: int = 2,
        head_dim: int = 128,
        seed: int = 42,
    ):
        self.layer_idx = layer_idx
        self.bit_width = bit_width
        self.is_boundary = (
            layer_idx < boundary_layers or
            layer_idx >= num_layers - boundary_layers
        )
        self.head_dim = head_dim
        self.offset = 0

        if self.is_boundary:
            # Full precision storage
            self.keys = None
            self.values = None
        else:
            # Compressed storage: lists of (indices, norms) per token
            self._k_indices = []  # list of (B, n_heads, head_dim) int arrays
            self._k_norms = []    # list of (B, n_heads) float arrays
            self._v_indices = []
            self._v_norms = []
            self._k_quantizer = MLXPolarQuant(head_dim, bit_width=bit_width, seed=seed + layer_idx)
            self._v_quantizer = MLXPolarQuant(head_dim, bit_width=bit_width, seed=seed + layer_idx + 1000)

    def update_and_fetch(self, keys, values):
        """Update cache and return full (potentially dequantized) cache.

        Args:
            keys: (B, n_kv_heads, num_new_tokens, head_dim)
            values: Same shape.

        Returns:
            (all_keys, all_values): Full cache up to current offset.
        """
        if self.is_boundary:
            return self._update_full_precision(keys, values)
        return self._update_compressed(keys, values)

    def _update_full_precision(self, keys, values):
        """Standard KVCache behavior for boundary layers."""
        prev = self.offset
        if self.keys is None or (prev + keys.shape[2]) > self.keys.shape[2]:
            B, n_kv_heads, _, k_head_dim = keys.shape
            v_head_dim = values.shape[3]
            n_steps = (self.step + keys.shape[2] - 1) // self.step
            k_shape = (B, n_kv_heads, n_steps * self.step, k_head_dim)
            v_shape = (B, n_kv_heads, n_steps * self.step, v_head_dim)
            new_k = mx.zeros(k_shape, keys.dtype)
            new_v = mx.zeros(v_shape, values.dtype)
            if self.keys is not None:
                if prev % self.step != 0:
                    self.keys = self.keys[..., :prev, :]
                    self.values = self.values[..., :prev, :]
                self.keys = mx.concatenate([self.keys, new_k], axis=2)
                self.values = mx.concatenate([self.values, new_v], axis=2)
            else:
                self.keys, self.values = new_k, new_v

        self.offset += keys.shape[2]
        self.keys[..., prev:self.offset, :] = keys
        self.values[..., prev:self.offset, :] = values
        return self.keys[..., :self.offset, :], self.values[..., :self.offset, :]

    def _update_compressed(self, keys, values):
        """TurboQuant-compressed update for middle layers."""
        B, n_kv_heads, num_new, head_dim = keys.shape

        for t in range(num_new):
            # keys[:, :, t, :] shape: (B, n_kv_heads, head_dim)
            k_t = keys[:, :, t, :]
            v_t = values[:, :, t, :]

            # Quantize each batch x head independently
            # Reshape to (B * n_kv_heads, head_dim) for batch quantization
            k_flat = k_t.reshape(-1, head_dim)
            v_flat = v_t.reshape(-1, head_dim)

            k_idx, k_nrm = self._k_quantizer.quantize(k_flat)
            v_idx, v_nrm = self._v_quantizer.quantize(v_flat)

            # Store as (B, n_kv_heads, ...) shapes
            self._k_indices.append(k_idx.reshape(B, n_kv_heads, head_dim))
            self._k_norms.append(k_nrm.reshape(B, n_kv_heads))
            self._v_indices.append(v_idx.reshape(B, n_kv_heads, head_dim))
            self._v_norms.append(v_nrm.reshape(B, n_kv_heads))

        self.offset += num_new

        # Dequantize entire cache for attention computation
        return self._dequantize_all()

    def _dequantize_all(self):
        """Dequantize all stored compressed tokens."""
        if not self._k_indices:
            return None, None

        seq_len = len(self._k_indices)
        B, n_kv_heads, head_dim = self._k_indices[0].shape

        # Stack all tokens: (seq_len, B, n_kv_heads, head_dim)
        all_k_idx = mx.stack(self._k_indices)
        all_k_nrm = mx.stack(self._k_norms)
        all_v_idx = mx.stack(self._v_indices)
        all_v_nrm = mx.stack(self._v_norms)

        # Flatten for batch dequantize: (seq * B * n_heads, head_dim)
        k_flat_idx = all_k_idx.reshape(-1, head_dim)
        k_flat_nrm = all_k_nrm.reshape(-1)
        v_flat_idx = all_v_idx.reshape(-1, head_dim)
        v_flat_nrm = all_v_nrm.reshape(-1)

        k_deq = self._k_quantizer.dequantize(k_flat_idx, k_flat_nrm)
        v_deq = self._v_quantizer.dequantize(v_flat_idx, v_flat_nrm)

        # Reshape back: (B, n_kv_heads, seq_len, head_dim)
        k_out = k_deq.reshape(seq_len, B, n_kv_heads, head_dim).transpose(1, 2, 0, 3)
        v_out = v_deq.reshape(seq_len, B, n_kv_heads, head_dim).transpose(1, 2, 0, 3)

        return k_out, v_out

    def make_mask(self, N, return_array=False, window_size=None):
        """Create attention mask (delegates to standard implementation)."""
        from mlx_lm.models.cache import create_attention_mask
        return create_attention_mask(N, self.offset, return_array=return_array, window_size=window_size)

    def is_trimmable(self):
        return True

    def trim(self, n):
        n = min(self.offset, n)
        self.offset -= n
        if self.is_boundary:
            pass  # offset tracks the trim
        else:
            # Remove last n compressed tokens
            for _ in range(n):
                if self._k_indices:
                    self._k_indices.pop()
                    self._k_norms.pop()
                    self._v_indices.pop()
                    self._v_norms.pop()
        return n

    def empty(self):
        if self.is_boundary:
            return self.keys is None
        return len(self._k_indices) == 0

    def size(self):
        return self.offset

    @property
    def state(self):
        if self.is_boundary:
            if self.keys is None:
                return []
            return self.keys[..., :self.offset, :], self.values[..., :self.offset, :]
        # For compressed layers, return dequantized state
        k, v = self._dequantize_all()
        if k is None:
            return []
        return k, v

    @state.setter
    def state(self, v):
        if not v:
            return
        if self.is_boundary:
            self.keys, self.values = v
            self.offset = self.keys.shape[-2]

    @property
    def meta_state(self):
        return str(self.offset)

    @meta_state.setter
    def meta_state(self, v):
        if v:
            self.offset = int(v)

    @property
    def nbytes(self):
        """Return theoretical bit-packed memory size.

        Indices are stored as int32 in MLX for computation, but the
        actual information content is bit_width bits per value.
        This reports the true compressed size (bit-packed equivalent).
        """
        if self.is_boundary:
            if self.keys is None:
                return 0
            return self.keys[..., :self.offset, :].nbytes + self.values[..., :self.offset, :].nbytes
        n = len(self._k_indices)
        if n == 0:
            return 0
        # Theoretical: bit_width bits per index value + 32-bit norm per vector
        B_heads = self._k_indices[0].shape[0] * self._k_indices[0].shape[1]  # B * n_kv_heads
        per_token_bits = B_heads * self.head_dim * self.bit_width * 2  # K + V indices
        per_token_norm_bits = B_heads * 32 * 2  # K + V norms (float32)
        total_bits = n * (per_token_bits + per_token_norm_bits)
        return total_bits // 8


def make_turbo_prompt_cache(model, bit_width=4, boundary_layers=2, seed=42):
    """Create TurboQuant KV cache for an mlx-lm model.

    Drop-in replacement for mlx_lm.models.cache.make_prompt_cache().

    Args:
        model: mlx-lm model with .layers attribute.
        bit_width: Quantization bits (3 or 4 recommended).
        boundary_layers: Number of layers at start/end to keep full precision.
        seed: Random seed for rotation matrices.

    Returns:
        List of TurboQuantKVCache, one per layer.
    """
    num_layers = len(model.layers)

    # Detect head_dim from model config
    head_dim = 128  # default
    if hasattr(model, 'args') and hasattr(model.args, 'head_dim'):
        head_dim = model.args.head_dim
    elif hasattr(model, 'config') and hasattr(model.config, 'head_dim'):
        head_dim = model.config.head_dim

    return [
        TurboQuantKVCache(
            layer_idx=i,
            num_layers=num_layers,
            bit_width=bit_width,
            boundary_layers=boundary_layers,
            head_dim=head_dim,
            seed=seed,
        )
        for i in range(num_layers)
    ]
