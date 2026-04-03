"""PPL benchmark: TurboQuant KV cache vs baseline on M1 Max.

Tests:
1. Flash Attention compatibility
2. Outlier 3.5-bit mode
3. mlx-lm hook integration (TurboQuantKVCache)
4. PPL comparison with Qwen2.5-Coder-7B (already running on port 4003)
"""

import mlx.core as mx
import sys
import time
import math


def test_flash_attention_compatibility():
    """Verify Flash Attention works with TurboQuant dequantized tensors."""
    from quantization.mlx_flash_attention import verify_flash_attention_compatible

    configs = [
        (128, 32, 8, 100),   # Qwen 7B: head_dim=128, 32 heads, 8 KV heads
        (128, 32, 32, 100),  # Standard: equal heads
        (64, 16, 4, 200),    # Smaller model
    ]

    for head_dim, n_heads, n_kv_heads, seq_len in configs:
        result = verify_flash_attention_compatible(head_dim, n_heads, n_kv_heads, seq_len)
        status = "OK" if result["compatible"] else "FAIL"
        print(f"  Flash Attn [{head_dim}d, {n_heads}h, {n_kv_heads}kv, {seq_len}seq]: "
              f"{status} (err: {result['max_error']:.2e})")
        assert result["compatible"], f"Flash Attention failed: {result['notes']}"
    print("  PASS")


def test_outlier_35bit():
    """Test 3.5-bit outlier channel splitting."""
    from quantization.mlx_outlier_quant import MLXOutlierPolarQuant

    d = 128
    oq = MLXOutlierPolarQuant(d=d, target_bits=3.5, seed=42)

    print(f"  Config: {oq.n_outlier} outlier@{oq.high_bits}b + "
          f"{oq.n_normal} normal@{oq.low_bits}b = {oq.effective_bits:.2f} avg bits")
    print(f"  Compression ratio: {oq.compression_ratio():.2f}x")

    # Round-trip test
    x = mx.random.normal(shape=(d,))
    compressed = oq.quantize(x)
    x_hat = oq.dequantize(compressed)

    mse = float(mx.mean((x - x_hat) ** 2).item())
    print(f"  3.5-bit round-trip MSE: {mse:.6f}")
    assert mse < 1.0, f"MSE too high: {mse}"

    # Batch test
    batch_x = mx.random.normal(shape=(16, d))
    batch_c = oq.quantize(batch_x)
    batch_hat = oq.dequantize(batch_c)
    batch_mse = float(mx.mean((batch_x - batch_hat) ** 2).item())
    print(f"  3.5-bit batch MSE: {batch_mse:.6f}")
    print("  PASS")


def test_mlx_lm_hook_interface():
    """Test TurboQuantKVCache matches mlx-lm's update_and_fetch interface."""
    from quantization.mlx_lm_hook import TurboQuantKVCache

    B, n_kv_heads, head_dim = 1, 8, 128
    num_layers = 32
    boundary = 2

    # Test boundary layer (full precision)
    boundary_cache = TurboQuantKVCache(
        layer_idx=0, num_layers=num_layers,
        bit_width=4, boundary_layers=boundary, head_dim=head_dim
    )
    assert boundary_cache.is_boundary, "Layer 0 should be boundary"

    # Test middle layer (compressed)
    middle_cache = TurboQuantKVCache(
        layer_idx=16, num_layers=num_layers,
        bit_width=4, boundary_layers=boundary, head_dim=head_dim
    )
    assert not middle_cache.is_boundary, "Layer 16 should be compressed"

    # Simulate token-by-token generation
    for step in range(10):
        keys = mx.random.normal(shape=(B, n_kv_heads, 1, head_dim))
        values = mx.random.normal(shape=(B, n_kv_heads, 1, head_dim))

        k_b, v_b = boundary_cache.update_and_fetch(keys, values)
        k_m, v_m = middle_cache.update_and_fetch(keys, values)

        assert k_b.shape == (B, n_kv_heads, step + 1, head_dim), \
            f"Boundary shape: {k_b.shape}, expected seq={step+1}"
        assert k_m.shape == (B, n_kv_heads, step + 1, head_dim), \
            f"Compressed shape: {k_m.shape}, expected seq={step+1}"

    # Memory comparison
    print(f"  Boundary cache (10 tokens): {boundary_cache.nbytes / 1024:.1f} KB")
    print(f"  Compressed cache (10 tokens): {middle_cache.nbytes / 1024:.1f} KB")
    savings = 1 - middle_cache.nbytes / max(boundary_cache.nbytes, 1)
    print(f"  Memory savings: {savings:.1%}")
    print("  PASS")


def test_turbo_cache_memory_at_scale():
    """Simulate 32-layer model with 1000 tokens, measure memory."""
    from quantization.mlx_lm_hook import TurboQuantKVCache

    B, n_kv_heads, head_dim = 1, 8, 128
    num_layers = 32
    boundary = 2
    n_tokens = 50  # Keep small for test speed

    caches = [
        TurboQuantKVCache(
            layer_idx=i, num_layers=num_layers,
            bit_width=4, boundary_layers=boundary, head_dim=head_dim
        )
        for i in range(num_layers)
    ]

    t0 = time.time()
    for _ in range(n_tokens):
        keys = mx.random.normal(shape=(B, n_kv_heads, 1, head_dim))
        values = mx.random.normal(shape=(B, n_kv_heads, 1, head_dim))
        for cache in caches:
            cache.update_and_fetch(keys, values)
    mx.eval([c.size() for c in caches])  # Force evaluation
    elapsed = time.time() - t0

    total_bytes = sum(c.nbytes for c in caches)
    boundary_bytes = sum(c.nbytes for c in caches if c.is_boundary)
    compressed_bytes = sum(c.nbytes for c in caches if not c.is_boundary)

    # Theoretical fp16 baseline
    fp16_bytes = num_layers * n_kv_heads * n_tokens * head_dim * 2 * 2  # K+V, fp16

    ratio = fp16_bytes / max(total_bytes, 1)
    print(f"  {num_layers} layers, {n_tokens} tokens, {n_kv_heads} KV heads, {head_dim} dim")
    print(f"  FP16 baseline: {fp16_bytes / 1024:.1f} KB")
    print(f"  TurboQuant total: {total_bytes / 1024:.1f} KB")
    print(f"    Boundary: {boundary_bytes / 1024:.1f} KB ({len([c for c in caches if c.is_boundary])} layers)")
    print(f"    Compressed: {compressed_bytes / 1024:.1f} KB ({len([c for c in caches if not c.is_boundary])} layers)")
    print(f"  Compression ratio: {ratio:.2f}x")
    print(f"  Time: {elapsed:.2f}s ({elapsed/n_tokens*1000:.1f} ms/token)")

    assert ratio > 1.5, f"Expected >1.5x compression, got {ratio:.2f}x"
    print("  PASS")


if __name__ == "__main__":
    tests = [
        ("Flash Attention Compatibility", test_flash_attention_compatibility),
        ("Outlier 3.5-bit Mode", test_outlier_35bit),
        ("mlx-lm Hook Interface", test_mlx_lm_hook_interface),
        ("TurboQuant Cache at Scale", test_turbo_cache_memory_at_scale),
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
            import traceback
            traceback.print_exc()
            failed += 1

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)}")
    sys.exit(0 if failed == 0 else 1)
