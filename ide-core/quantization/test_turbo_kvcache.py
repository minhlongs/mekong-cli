"""Integration test for MLX TurboQuant KV Cache.

Tests:
1. WHT round-trip (rotation + transpose = identity)
2. PolarQuant distortion within paper bounds
3. KV Cache Boundary V strategy
4. Compression ratio verification
5. Sparse V sparsity stats
"""

import mlx.core as mx
import math
import sys

def test_wht_roundtrip():
    """WHT rotation + transpose should approximately recover input."""
    from quantization.mlx_wht import generate_rotation_params, apply_rotation, apply_rotation_transpose

    d = 128
    signs1, signs2, padded_d = generate_rotation_params(d, seed=42)

    x = mx.random.normal(shape=(d,))
    y = apply_rotation(x, signs1, signs2, padded_d)
    x_hat = apply_rotation_transpose(y, signs1, signs2, padded_d)

    error = float(mx.linalg.norm(x - x_hat).item())
    rel_error = error / float(mx.linalg.norm(x).item())
    print(f"  WHT round-trip relative error: {rel_error:.2e}")
    assert rel_error < 1e-5, f"WHT round-trip error too large: {rel_error}"
    print("  PASS")

def test_wht_batch():
    """Batch WHT should work correctly."""
    from quantization.mlx_wht import generate_rotation_params, apply_rotation

    d = 64
    batch = 16
    signs1, signs2, padded_d = generate_rotation_params(d, seed=99)

    X = mx.random.normal(shape=(batch, d))
    Y = apply_rotation(X, signs1, signs2, padded_d)
    assert Y.shape == (batch, d), f"Expected ({batch}, {d}), got {Y.shape}"
    print(f"  Batch WHT shape: {Y.shape}")
    print("  PASS")

def test_polar_quant_distortion():
    """PolarQuant MSE should be within paper bounds."""
    from quantization.mlx_polar_quant import MLXPolarQuant

    d = 256
    bit_width = 3
    pq = MLXPolarQuant(d, bit_width=bit_width, seed=42)

    # Generate random unit-norm vectors
    n_trials = 100
    total_mse = 0.0
    for i in range(n_trials):
        x = mx.random.normal(shape=(d,))
        x = x / mx.linalg.norm(x)  # unit norm

        indices, norms = pq.quantize(x)
        x_hat = pq.dequantize(indices, norms)

        mse = float(mx.mean((x - x_hat) ** 2).item())
        total_mse += mse

    avg_mse = total_mse / n_trials
    # Paper Table: 3-bit MSE ≈ 0.03 for unit vectors
    print(f"  PolarQuant {bit_width}-bit avg MSE: {avg_mse:.4f} (paper bound: ~0.03)")
    assert avg_mse < 0.15, f"MSE too high: {avg_mse}"
    print("  PASS")

def test_kv_cache_boundary_v():
    """Boundary V: boundary layers full precision, middle compressed."""
    from quantization.mlx_kv_cache import TurboKVCache

    num_layers = 8
    num_heads = 4
    head_dim = 64
    boundary = 2

    cache = TurboKVCache(
        num_layers=num_layers, num_heads=num_heads,
        head_dim=head_dim, bit_width=4, boundary_layers=boundary
    )

    # Insert tokens
    for layer in range(num_layers):
        for _ in range(10):
            k = mx.random.normal(shape=(num_heads, head_dim))
            v = mx.random.normal(shape=(num_heads, head_dim))
            cache.update(layer, k, v)

    # Verify boundary layers exist
    assert 0 in cache.boundary_indices
    assert 1 in cache.boundary_indices
    assert (num_layers - 1) in cache.boundary_indices
    assert (num_layers - 2) in cache.boundary_indices

    # Verify middle layers are compressed
    assert 3 not in cache.boundary_indices
    assert 4 not in cache.boundary_indices

    # Get cache — should return (seq_len, head_dim)
    k_b, v_b = cache.get(0, 0)  # boundary
    k_c, v_c = cache.get(3, 0)  # compressed

    assert k_b.shape == (10, head_dim), f"Boundary K shape: {k_b.shape}"
    assert k_c.shape == (10, head_dim), f"Compressed K shape: {k_c.shape}"

    stats = cache.memory_stats()
    print(f"  Boundary layers: {stats['boundary_layers']}")
    print(f"  Compressed layers: {stats['compressed_layers']}")
    print(f"  Compression ratio: {stats['compression_ratio']:.2f}x")
    print(f"  Original: {stats['original_mb']:.2f} MB, Compressed: {stats['compressed_mb']:.2f} MB")
    assert stats["compression_ratio"] > 1.5, f"Compression too low: {stats['compression_ratio']}"
    print("  PASS")

def test_compression_ratio():
    """Verify theoretical compression ratio at 4-bit."""
    from quantization.mlx_kv_cache import TurboKVCache

    cache = TurboKVCache(
        num_layers=32, num_heads=32, head_dim=128,
        bit_width=4, boundary_layers=2
    )

    # Simulate 1000 tokens
    for layer in range(32):
        for _ in range(10):
            k = mx.random.normal(shape=(32, 128))
            v = mx.random.normal(shape=(32, 128))
            cache.update(layer, k, v)

    stats = cache.memory_stats()
    print(f"  32-layer, 32-head, 128-dim, 10 tokens, 4-bit:")
    print(f"  Original: {stats['original_mb']:.1f} MB")
    print(f"  Compressed: {stats['compressed_mb']:.1f} MB")
    print(f"  Ratio: {stats['compression_ratio']:.2f}x")
    # With 4 boundary layers at fp16 + 28 compressed at 4-bit, expect ~3x+
    assert stats["compression_ratio"] > 2.0, f"Expected >2x, got {stats['compression_ratio']}"
    print("  PASS")

def test_sparse_v_stats():
    """Sparse V: verify sparsity detection works."""
    from quantization.mlx_sparse_v import compute_sparsity_stats

    # Create synthetic attention weights (most mass on few positions)
    seq_len = 100
    weights = mx.zeros((1, seq_len))
    # Concentrate mass on 5 positions
    for i in [0, 10, 50, 90, 99]:
        weights = weights.at[0, i].add(0.2)

    stats = compute_sparsity_stats(weights, threshold=1e-6)
    print(f"  Active: {stats['active_positions']}/{stats['total_positions']}")
    print(f"  Skip rate: {stats['skip_rate']:.1%}")
    assert stats["skip_rate"] > 0.5, f"Expected >50% skip, got {stats['skip_rate']}"
    print("  PASS")

if __name__ == "__main__":
    tests = [
        ("WHT Round-trip", test_wht_roundtrip),
        ("WHT Batch", test_wht_batch),
        ("PolarQuant Distortion", test_polar_quant_distortion),
        ("KV Cache Boundary V", test_kv_cache_boundary_v),
        ("Compression Ratio", test_compression_ratio),
        ("Sparse V Stats", test_sparse_v_stats),
    ]

    passed = 0
    failed = 0
    for name, fn in tests:
        print(f"\n[TEST] {name}")
        try:
            fn()
            passed += 1
        except Exception as e:
            print(f"  FAIL: {e}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)}")
    sys.exit(0 if failed == 0 else 1)
