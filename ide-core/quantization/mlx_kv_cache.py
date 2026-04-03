"""Unified TurboQuant KV Cache for Mekong IDE on MLX.

Implements the Boundary V strategy from the implementation plan:
- First 2 + last 2 layers: keep full precision (float16/int8)
- Middle layers: compress with TurboQuant at 3.5 bits/value

This achieves 40-60% RAM reduction while maintaining coherent output
(< 5% PPL degradation per Boundary V benchmarks).

Hooks into mlx-lm's KV cache at the update_cache level.
"""

import mlx.core as mx
from dataclasses import dataclass, field

from quantization.mlx_polar_quant import MLXPolarQuant


@dataclass
class CompressedLayer:
    """Compressed KV for a single layer."""
    k_indices: list[mx.array] = field(default_factory=list)  # per-head: (seq, d)
    k_norms: list[mx.array] = field(default_factory=list)    # per-head: (seq,)
    v_indices: list[mx.array] = field(default_factory=list)
    v_norms: list[mx.array] = field(default_factory=list)


class TurboKVCache:
    """Unified KV Cache with Boundary V compression.

    Usage:
        cache = TurboKVCache(
            num_layers=32, num_heads=32, head_dim=128,
            bit_width=4, boundary_layers=2
        )

        # During prefill/decode, hook into each layer:
        for layer_idx in range(num_layers):
            k, v = model_layer(x)  # raw K, V tensors
            cache.update(layer_idx, k, v)

        # During attention:
        for layer_idx in range(num_layers):
            k_cache, v_cache = cache.get(layer_idx, head_idx)
            # k_cache, v_cache are already dequantized
    """

    def __init__(
        self,
        num_layers: int,
        num_heads: int,
        head_dim: int,
        bit_width: int = 4,
        boundary_layers: int = 2,
        seed: int = 42,
    ):
        self.num_layers = num_layers
        self.num_heads = num_heads
        self.head_dim = head_dim
        self.bit_width = bit_width
        self.boundary_layers = boundary_layers

        # Boundary layer indices (first N + last N keep full precision)
        self.boundary_indices = set(
            list(range(boundary_layers)) +
            list(range(num_layers - boundary_layers, num_layers))
        )

        # Quantizer for compressed layers (shared across all heads/layers)
        # K cache uses bit_width for inner product preservation
        self.k_quantizer = MLXPolarQuant(head_dim, bit_width=bit_width, seed=seed)
        # V cache uses bit_width for MSE preservation
        self.v_quantizer = MLXPolarQuant(head_dim, bit_width=bit_width, seed=seed + 500)

        # Storage
        self.full_k: dict[int, list[list[mx.array]]] = {}  # layer -> [head -> [tokens]]
        self.full_v: dict[int, list[list[mx.array]]] = {}
        self.compressed: dict[int, CompressedLayer] = {}

        self._init_storage()

    def _init_storage(self):
        for layer in range(self.num_layers):
            if layer in self.boundary_indices:
                self.full_k[layer] = [[] for _ in range(self.num_heads)]
                self.full_v[layer] = [[] for _ in range(self.num_heads)]
            else:
                self.compressed[layer] = CompressedLayer(
                    k_indices=[[] for _ in range(self.num_heads)],
                    k_norms=[[] for _ in range(self.num_heads)],
                    v_indices=[[] for _ in range(self.num_heads)],
                    v_norms=[[] for _ in range(self.num_heads)],
                )

    def update(self, layer_idx: int, k: mx.array, v: mx.array):
        """Update cache for a layer. Called during prefill/decode.

        Args:
            layer_idx: Layer index.
            k: Key tensor, shape (num_heads, seq_new, head_dim) or (num_heads, head_dim).
            v: Value tensor, same shape.
        """
        if k.ndim == 2:
            k = k[:, None, :]  # (num_heads, 1, head_dim)
            v = v[:, None, :]

        num_heads, seq_new, head_dim = k.shape

        if layer_idx in self.boundary_indices:
            # Full precision — just append
            for h in range(num_heads):
                for t in range(seq_new):
                    self.full_k[layer_idx][h].append(k[h, t])
                    self.full_v[layer_idx][h].append(v[h, t])
        else:
            # Compress on the fly
            comp = self.compressed[layer_idx]
            for h in range(num_heads):
                for t in range(seq_new):
                    k_idx, k_norm = self.k_quantizer.quantize(k[h, t])
                    v_idx, v_norm = self.v_quantizer.quantize(v[h, t])
                    comp.k_indices[h].append(k_idx)
                    comp.k_norms[h].append(k_norm)
                    comp.v_indices[h].append(v_idx)
                    comp.v_norms[h].append(v_norm)

    def get(self, layer_idx: int, head_idx: int) -> tuple[mx.array, mx.array]:
        """Get K, V cache for a layer/head, dequantized if compressed.

        Returns:
            (k_cache, v_cache): both shape (seq_len, head_dim).
        """
        if layer_idx in self.boundary_indices:
            k_list = self.full_k[layer_idx][head_idx]
            v_list = self.full_v[layer_idx][head_idx]
            if not k_list:
                return mx.zeros((0, self.head_dim)), mx.zeros((0, self.head_dim))
            return mx.stack(k_list), mx.stack(v_list)
        else:
            comp = self.compressed[layer_idx]
            if not comp.k_indices[head_idx]:
                return mx.zeros((0, self.head_dim)), mx.zeros((0, self.head_dim))

            k_idx = mx.stack(comp.k_indices[head_idx])
            k_nrm = mx.stack(comp.k_norms[head_idx])
            v_idx = mx.stack(comp.v_indices[head_idx])
            v_nrm = mx.stack(comp.v_norms[head_idx])

            k_deq = self.k_quantizer.dequantize(k_idx, k_nrm)
            v_deq = self.v_quantizer.dequantize(v_idx, v_nrm)
            return k_deq, v_deq

    def get_v_compressed(self, layer_idx: int, head_idx: int) -> tuple[mx.array, mx.array]:
        """Get raw compressed V (for Sparse V optimization).

        Returns:
            (v_indices, v_norms) or None if boundary layer.
        """
        if layer_idx in self.boundary_indices:
            return None, None
        comp = self.compressed[layer_idx]
        if not comp.v_indices[head_idx]:
            return mx.zeros((0, self.head_dim), dtype=mx.int32), mx.zeros((0,))
        return mx.stack(comp.v_indices[head_idx]), mx.stack(comp.v_norms[head_idx])

    def seq_len(self, layer_idx: int = 0) -> int:
        """Current sequence length."""
        if layer_idx in self.boundary_indices:
            if self.full_k[layer_idx][0]:
                return len(self.full_k[layer_idx][0])
            return 0
        comp = self.compressed[layer_idx]
        if comp.k_indices[0]:
            return len(comp.k_indices[0])
        return 0

    def memory_stats(self) -> dict:
        """Compute memory usage statistics."""
        boundary_count = 0
        compressed_count = 0

        for layer in range(self.num_layers):
            tokens = self.seq_len(layer)
            vectors = tokens * self.num_heads
            if layer in self.boundary_indices:
                boundary_count += vectors
            else:
                compressed_count += vectors

        fp16_bytes = (boundary_count + compressed_count) * self.head_dim * 2  # K+V
        # Compressed: bit_width bits per value + 32-bit norm per vector
        compressed_bits = compressed_count * (self.head_dim * self.bit_width + 32) * 2  # K+V
        boundary_bits = boundary_count * self.head_dim * 16 * 2  # K+V in fp16

        actual_bytes = (compressed_bits + boundary_bits) / 8
        original_bytes = fp16_bytes * 2  # K+V both in fp16

        return {
            "original_mb": original_bytes / 1024 / 1024,
            "compressed_mb": actual_bytes / 1024 / 1024,
            "compression_ratio": original_bytes / max(actual_bytes, 1),
            "boundary_layers": len(self.boundary_indices),
            "compressed_layers": self.num_layers - len(self.boundary_indices),
            "total_tokens": self.seq_len(),
            "bit_width": self.bit_width,
        }
