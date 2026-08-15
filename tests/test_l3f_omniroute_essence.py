"""Tests cho 7 tinh hoa OmniRoute v3.8.50 port vào mk7:

A1 provider breaker + cooldown retry · A2 spend/burn-rate · A3 watchdog ·
B4 model-family fallback · B5 session affinity pin · B6 compression pipeline ·
B7 learned rate limits + health per model.

Tất cả offline — không gọi gateway thật (mock _attempt / ping).
"""
import io
import os
import socket
import sys
import tempfile
import time
import urllib.error
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.mk7.core.llm import (STALL_ALERTS, LLMClient, LLMError,
                              effective_model_with_pin)
from src.mk7.core.models import (BANNED_MODEL_KEYS, MODEL_FAMILIES,
                                 fallback_chain, family_of, resolve_or_fallback)
from src.mk7.core.resilience import (BACKOFF_STEPS_S, RETRY_BUDGET_MS, Breaker,
                                     parse_retry_after_seconds)


def _patch_state_dir(td: str):
    from src.mk7.core import opc_loop as m

    old = m._state_dir
    m._state_dir = lambda: Path(td)  # noqa: E731
    return old


def _http_429(body: str) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        "http://gateway/api/v1/chat/completions", 429, "Too Many Requests",
        None, io.BytesIO(body.encode()),
    )


def _raise_429(body: str):
    raise _http_429(body)


def _ok_response(content: str = "hi") -> dict:
    return {
        "choices": [{"message": {"content": content}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
    }


# ── A1: breaker ──────────────────────────────────────────────

def test_breaker_budget_and_backoff_steps():
    assert RETRY_BUDGET_MS == 60_000
    assert BACKOFF_STEPS_S == (30, 60, 120)


def test_breaker_record_expire_success():
    with tempfile.TemporaryDirectory() as td:
        br = Breaker(path=Path(td) / "breaker.json")
        assert not br.is_locked("p", "m")
        br.record_failure("p", "m")
        assert br.is_locked("p", "m")
        assert 29 <= br.remaining("p", "m") <= 30
        br.record_success("p", "m")
        assert not br.is_locked("p", "m")


def test_breaker_exponential_backoff():
    with tempfile.TemporaryDirectory() as td:
        br = Breaker(path=Path(td) / "breaker.json")
        for step in (30, 60, 120):
            br.record_failure("p", "m")
            assert br.remaining("p", "m") >= step - 1  # tolerance micro-giây


def test_breaker_retry_after_priority_and_expiry():
    with tempfile.TemporaryDirectory() as td:
        br = Breaker(path=Path(td) / "breaker.json")
        br.record_failure("p", "m", retry_after=5)
        assert 4.5 <= br.remaining("p", "m") <= 5.0
        br.record_failure("p", "m2", retry_after=0.01)
        time.sleep(0.02)
        assert not br.is_locked("p", "m2")


def test_breaker_persists():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "breaker.json"
        Breaker(path=p).record_failure("p", "m", retry_after=3600)
        br2 = Breaker(path=p)
        assert br2.is_locked("p", "m")
        assert "m" in [d["model"] for d in br2.locked_models()]


def test_parse_retry_after_variants():
    assert parse_retry_after_seconds("Resets in 2 hours") == 7200
    assert parse_retry_after_seconds("Monthly limit reached. resets in 13 days") == 13 * 86400
    assert parse_retry_after_seconds("Resets in 30 minutes") == 1800
    assert parse_retry_after_seconds("reset after 45s") == 45
    assert parse_retry_after_seconds("Retry-After: 12") == 12
    assert parse_retry_after_seconds("all good") is None
    assert parse_retry_after_seconds(None) is None


# ── A2: spend ────────────────────────────────────────────────

def test_cost_estimate_table():
    from src.mk7.core.spend import cost_estimate

    assert cost_estimate("claude-opus-5", 1_000_000, 0) == 15.0
    assert cost_estimate("claude-fable-5", 0, 1_000_000) == 15.0
    assert cost_estimate("claude-haiku-4-5", 1_000_000, 0) == 1.0
    assert cost_estimate("deepseek-v4-flash", 1_000_000, 0) == 0.3
    assert cost_estimate("gpt-oss-20b:free", 1_000_000, 1_000_000) == 0.0
    assert cost_estimate("unknown-model", 1_000_000, 0) == 0.0


def test_spend_record_and_burn_rate():
    with tempfile.TemporaryDirectory() as td:
        old = _patch_state_dir(td)
        try:
            from src.mk7.core.spend import burn_rate, record_spend, spend_by_product

            record_spend("omnimbp.local", "claude-opus-5", 1_000_000, 0)
            record_spend("omnimbp.local", "claude-fable-5", 0, 1_000_000)
            record_spend("omnimbp.local", "deepseek-v4-flash", 1_000_000, 0)
            assert burn_rate(24) == 15.0 + 15.0 + 0.3
            assert burn_rate(24 * 7) == 15.0 + 15.0 + 0.3
            spend_by_product("sophia", hours=24) == []
            record_spend("p", "claude-fable-5", 100, 0, caller="sophia-cook")
            assert len(spend_by_product("sophia", hours=24)) == 1
        finally:
            from src.mk7.core import opc_loop as m

            m._state_dir = old


def test_chat_success_records_spend():
    with tempfile.TemporaryDirectory() as td:
        old = _patch_state_dir(td)
        try:
            client = LLMClient(breaker=Breaker(path=Path(td) / "b.json"))
            client._attempt = lambda body, timeout: _ok_response()  # noqa: E731
            client.chat("claude-fable-5", [{"role": "user", "content": "x"}])
            from src.mk7.core.spend import burn_rate

            expected = 3.0 * 10 / 1e6 + 15.0 * 5 / 1e6
            assert abs(burn_rate(24) - expected) < 1e-4
        finally:
            from src.mk7.core import opc_loop as m

            m._state_dir = old


# ── B4: family fallback ──────────────────────────────────────

def test_family_of():
    assert family_of("claude-opus-5") == "claude"
    assert family_of("deepseek-v4-flash") == "deepseek"
    assert family_of("qwen3.8-max") == "openrouter"
    assert family_of("claude-opus-4-8[1m]") == "claude"
    assert family_of("weird") is None


def test_fallback_chain_order_and_banned_guard():
    chain = fallback_chain("claude-opus-5")
    assert chain == [
        "claude-sonnet-5", "claude-opus-4-6", "claude-fable-5",
        "deepseek-v4-pro", "deepseek-v4-flash", "deepseek-v4-flash2",
        "gpt-oss-20b:free", "nemotron-3-ultra-550b-a55b:free",
    ]
    assert not any(m in BANNED_MODEL_KEYS for m in chain)
    # chain từ qwen cũng không bao giờ chứa qwen (banned)
    qwen_chain = fallback_chain("qwen3.8-max")
    assert "qwen3.8-max" not in qwen_chain
    assert not any(m in BANNED_MODEL_KEYS for m in qwen_chain)
    # đủ model theo spec
    assert sum(len(v) for v in MODEL_FAMILIES.values()) >= 9


def test_resolve_or_fallback_locked_uses_sibling():
    locked = {"claude-opus-5", "claude-sonnet-5", "claude-opus-4-6", "claude-fable-5"}
    entry = resolve_or_fallback("claude-opus-5", locked=lambda m: m in locked)
    assert entry.id == "deepseek-v4-pro"
    assert entry.id not in BANNED_MODEL_KEYS


def test_resolve_or_fallback_banned_still_fable():
    entry = resolve_or_fallback("strategist")
    assert entry.id == "claude-fable-5"
    entry2 = resolve_or_fallback("qwen3.8-max", locked=lambda m: False)
    assert entry2.id == "claude-fable-5"


# ── B4 + A1: chat dùng family khi locked ─────────────────────

def test_chat_locked_model_uses_family_sibling():
    with tempfile.TemporaryDirectory() as td:
        _patch_state_dir(td)
        br = Breaker(path=Path(td) / "b.json")
        br.record_failure("omnimbp.local", "claude-fable-5", retry_after=3600)
        client = LLMClient(base_url="http://omnimbp.local:8000/v1", breaker=br)
        called: list[str] = []
        client._attempt = lambda body, timeout: called.append(body["model"]) or _ok_response()  # noqa: E731
        client.chat("claude-fable-5", [{"role": "user", "content": "x"}])
        assert called[0] == "claude-sonnet-5"  # sibling đầu tiên chưa locked (opus-5 banned)
        assert "qwen3.8-max" not in called


def test_chat_banned_model_never_called():
    with tempfile.TemporaryDirectory() as td:
        _patch_state_dir(td)
        client = LLMClient(breaker=Breaker(path=Path(td) / "b.json"))
        called: list[str] = []
        client._attempt = lambda body, timeout: called.append(body["model"]) or _ok_response()  # noqa: E731
        client.chat("strategist", [{"role": "user", "content": "x"}])
        assert called == ["claude-fable-5"]


def test_chat_all_locked_raises():
    with tempfile.TemporaryDirectory() as td:
        _patch_state_dir(td)
        br = Breaker(path=Path(td) / "b.json")
        for m in ("claude-fable-5", "claude-opus-5", "claude-sonnet-5", "claude-opus-4-6",
                  "deepseek-v4-pro", "deepseek-v4-flash", "deepseek-v4-flash2",
                  "gpt-oss-20b:free", "nemotron-3-ultra-550b-a55b:free"):
            br.record_failure("omnimbp.local", m, retry_after=3600)
        client = LLMClient(breaker=br)
        try:
            client.chat("claude-fable-5", [{"role": "user", "content": "x"}])
            assert False, "phải raise khi mọi family model locked"
        except LLMError as e:
            assert "locked" in str(e)


# ── A1: cooldown-aware retry ─────────────────────────────────

def test_chat_cooldown_retry_then_success():
    with tempfile.TemporaryDirectory() as td:
        _patch_state_dir(td)
        client = LLMClient(breaker=Breaker(path=Path(td) / "b.json"), max_retries=2)
        attempts: list[str] = []
        client._attempt = lambda body, timeout: attempts.append(body["model"]) or (  # noqa: E731
            _raise_429("Rate limit reached. Resets in 1 second") if len(attempts) == 1
            else _ok_response()
        )
        data = client.chat("claude-fable-5", [{"role": "user", "content": "x"}])
        assert len(attempts) == 2
        assert data["choices"][0]["message"]["content"] == "hi"
        assert not client.breaker.is_locked("omnimbp.local", "claude-fable-5")


def test_chat_retry_budget_exhausted_raises():
    with tempfile.TemporaryDirectory() as td:
        _patch_state_dir(td)
        client = LLMClient(breaker=Breaker(path=Path(td) / "b.json"))
        client._attempt = lambda body, timeout: _raise_429("Quota. Resets in 2 hours")  # noqa: E731
        try:
            client.chat("claude-fable-5", [{"role": "user", "content": "x"}])
            assert False, "phải raise khi vượt retry budget 60s"
        except LLMError as e:
            assert "budget" in str(e)
        assert client.breaker.is_locked("omnimbp.local", "claude-fable-5")


# ── A3: watchdog ─────────────────────────────────────────────

def test_watchdog_stall_aborts_and_records_failure():
    with tempfile.TemporaryDirectory() as td:
        _patch_state_dir(td)
        del STALL_ALERTS[:]
        client = LLMClient(breaker=Breaker(path=Path(td) / "b.json"))

        def stall(body, timeout):  # noqa: ANN001
            raise socket.timeout("stalled")

        client._attempt = stall
        try:
            client.chat_with_watchdog(
                "claude-fable-5", [{"role": "user", "content": "x"}],
                stall_seconds=5, hard_timeout=10,
            )
            assert False, "phải raise khi stall"
        except LLMError as e:
            assert "stall" in str(e)
        assert client.breaker.is_locked("omnimbp.local", "claude-fable-5")
        assert any("stall" in a for a in STALL_ALERTS)


def test_watchdog_passthrough_success():
    with tempfile.TemporaryDirectory() as td:
        _patch_state_dir(td)
        client = LLMClient(breaker=Breaker(path=Path(td) / "b.json"))
        client._attempt = lambda body, timeout: _ok_response()  # noqa: E731
        data = client.chat_with_watchdog("claude-fable-5", [{"role": "user", "content": "x"}])
        assert data["choices"][0]["message"]["content"] == "hi"


# ── B5: session affinity pin ─────────────────────────────────

def test_session_pin_wins_while_alive():
    from src.mk7.core.session import Session

    s = Session(directory="/tmp")
    s.pin_model("claude-opus-5", duration_s=3600)
    assert s.pin_active()
    assert effective_model_with_pin(s, "claude-fable-5") == "claude-opus-5"


def test_session_pin_429_unpins():
    from src.mk7.core.session import Session

    s = Session(directory="/tmp")
    s.pin_model("claude-opus-5", duration_s=3600)
    s.unpin()  # 429 → unpin + ghi failure (sessionAffinityPin fix 3.8.50)
    assert not s.pin_active()
    assert s.provider_pin == ""
    assert effective_model_with_pin(s, "claude-fable-5") == "claude-fable-5"


def test_session_pin_expired():
    from src.mk7.core.session import Session

    s = Session(directory="/tmp")
    s.pin_model("claude-opus-5", duration_s=0.001)
    time.sleep(0.01)
    assert not s.pin_active()


def test_session_pin_fields_roundtrip():
    from src.mk7.core.session import Session

    s = Session(directory="/tmp")
    s.pin_model("claude-sonnet-5", duration_s=60)
    s.last_model = "claude-sonnet-5"
    d = s.to_dict()
    s2 = Session.from_dict(d)
    assert s2.provider_pin == "claude-sonnet-5"
    assert s2.last_model == "claude-sonnet-5"
    assert s2.unpin_after == d["unpin_after"]


def test_chat_pin_success_records_last_model():
    with tempfile.TemporaryDirectory() as td:
        _patch_state_dir(td)
        import src.mk7.core.session as sm

        old_dir, old_index = sm.SESSIONS_DIR, sm.INDEX_FILE
        sm.SESSIONS_DIR = Path(td) / "sessions"
        sm.INDEX_FILE = sm.SESSIONS_DIR / "index.json"
        try:
            store = sm.SessionStore()
            s = store.create("/tmp", agent_id="ceo", title="pin-test")
            s.pin_model("claude-opus-4-6", duration_s=3600)
            store.save(s)
            client = LLMClient(breaker=Breaker(path=Path(td) / "b.json"))
            called: list[str] = []
            client._attempt = lambda body, timeout: called.append(body["model"]) or _ok_response()  # noqa: E731
            client.chat("claude-fable-5", [{"role": "user", "content": "x"}], pin=s.id)
            assert called == ["claude-opus-4-6"]  # pin thắng forced
            assert store.get(s.id).last_model == "claude-opus-4-6"
        finally:
            sm.SESSIONS_DIR, sm.INDEX_FILE = old_dir, old_index


def test_chat_429_unpins_session():
    with tempfile.TemporaryDirectory() as td:
        _patch_state_dir(td)
        import src.mk7.core.session as sm

        old_dir, old_index = sm.SESSIONS_DIR, sm.INDEX_FILE
        sm.SESSIONS_DIR = Path(td) / "sessions"
        sm.INDEX_FILE = sm.SESSIONS_DIR / "index.json"
        try:
            store = sm.SessionStore()
            s = store.create("/tmp", agent_id="ceo", title="pin-429")
            s.pin_model("claude-opus-5", duration_s=3600)
            store.save(s)
            client = LLMClient(breaker=Breaker(path=Path(td) / "b.json"))
            client._attempt = lambda body, timeout: _raise_429("Resets in 2 hours")  # noqa: E731
            try:
                client.chat("claude-fable-5", [{"role": "user", "content": "x"}], pin=s.id)
            except LLMError:
                pass
            assert store.get(s.id).provider_pin == ""   # 429 → unpin
            assert not store.get(s.id).pin_active()
        finally:
            sm.SESSIONS_DIR, sm.INDEX_FILE = old_dir, old_index


# ── B6: compression pipeline ─────────────────────────────────

def test_compaction_lossless_reduces_50pct():
    from src.mk7.core.compaction import Compactor

    base = "".join(f"line {n} \x1b[31mRED\x1b[0m    \n" for n in range(150))
    shared = {"keep_1": base + "K1", "keep_2": base + "K2"}
    for i in range(18):
        shared[f"dup_{i}"] = base  # 18 blocks trùng hash
    c = Compactor()
    before, after = c.lossless(shared)
    assert before >= 20_000
    assert after <= before * 0.5
    assert c.should_compact(shared)


def test_compaction_bailout_skips_summarize():
    from src.mk7.core.compaction import Compactor

    class FakeClient:  # không được gọi khi bail-out
        def text(self, *a, **kw):  # noqa: ANN002, ANN003
            raise AssertionError("summarize không được gọi khi lossless ≥ 60%")

    base = "".join(f"line {n} \x1b[31mRED\x1b[0m    \n" for n in range(150))
    shared = {"keep_1": base + "K1", "keep_2": base + "K2"}
    for i in range(18):
        shared[f"dup_{i}"] = base
    c = Compactor(client=FakeClient(), threshold_chars=1000)  # type: ignore[arg-type]
    result = c.compact(shared)
    assert result.compacted
    assert not result.summarized                       # bail-out
    assert result.pipeline_reduced >= result.original_chars * 0.6


def test_compaction_summarizes_when_lossless_not_enough():
    from src.mk7.core.compaction import Compactor

    class FakeClient:
        def __init__(self):
            self.calls = 0

        def text(self, model, prompt, system=None, max_tokens=4096):  # noqa: ANN001
            self.calls += 1
            return "compact factual summary"

    fake = FakeClient()
    shared = {f"b{i}": f"unique block {i}: " + "x" * 300 for i in range(5)}  # 0% dup/ANSI
    c = Compactor(client=fake, threshold_chars=1000)  # type: ignore[arg-type]
    result = c.compact(shared)
    assert result.compacted
    assert result.summarized
    assert fake.calls == 1
    assert result.summary == "compact factual summary"


def test_compaction_should_not_compact_small():
    from src.mk7.core.compaction import Compactor

    c = Compactor()
    assert not c.should_compact({"a": "short context"})
    assert not c.compact({"a": "short context"}).compacted


# ── B7: learned rate limits + health per model ───────────────

def test_chat_429_learns_rate_limit():
    with tempfile.TemporaryDirectory() as td:
        _patch_state_dir(td)
        client = LLMClient(breaker=Breaker(path=Path(td) / "b.json"))
        client._attempt = lambda body, timeout: _raise_429(  # noqa: E731
            "Monthly usage limit reached. Resets in 2 hours"
        )
        try:
            client.chat("claude-fable-5", [{"role": "user", "content": "x"}])
        except LLMError:
            pass
        limits = client.breaker.rate_limits()
        assert "claude-fable-5" in limits
        assert limits["claude-fable-5"]["reset_in"] == 7200


def test_health_per_model_with_lockout():
    from src.mk7.core.omni import healthcheck_all

    with tempfile.TemporaryDirectory() as td:
        old = _patch_state_dir(td)
        try:
            from src.mk7.core.resilience import breaker

            client = LLMClient(timeout=5)
            client.ping = lambda model: (True, "ok (PONG)")  # noqa: E731
            results = healthcheck_all(client)
            assert len(results) == 2                      # fable + sonnet (opus banned)
            assert all(r["ok"] and not r["locked"] for r in results)
            breaker.record_failure("omnimbp.local", "claude-fable-5", retry_after=3600)
            results2 = healthcheck_all(client)
            fable = next(r for r in results2 if r["model"] == "claude-fable-5")
            assert fable["locked"] and not fable["ok"]
            assert fable["detail"].startswith("LOCKED")
            breaker.record_success("omnimbp.local", "claude-fable-5")
        finally:
            from src.mk7.core import opc_loop as m

            m._state_dir = old


if __name__ == "__main__":
    import traceback

    failed = total = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            total += 1
            try:
                fn()
                print(f"PASS {name}")
            except Exception:
                failed += 1
                print(f"FAIL {name}")
                traceback.print_exc()
    print(f"\n{total - failed}/{total} passed")
    sys.exit(1 if failed else 0)
