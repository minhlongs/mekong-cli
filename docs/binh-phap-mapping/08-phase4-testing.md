# Phase 4: Testing & Acceptance — Verification Protocol

> Status: DRAFT
> Prerequisite: Phase 1-3 complete

## 1. Test Pyramid

```
        /\
       /  \      E2E: Full vertical chain
      /----\     Integration: Dispatcher + topology
     /      \    Unit: escalation, routing, Jidoka
    /________\
```

## 2. Unit Tests (src/tests/)

### 2.1 test_binh_phap_escalation.py
```python
def test_resolve_llm_provider_strategic_returns_fable():
    config = resolve_llm_provider("strategic")
    assert config["model"] == "claude-fable-5"

def test_resolve_llm_provider_default_returns_opus():
    config = resolve_llm_provider("cloud_sonnet")
    assert config["model"] == "claude-opus-4-8"

def test_zunef_env_overrides_anthropic():
    os.environ["ZUNEF_FABLE_BASE_URL"] = "https://zunef.v2/api/v1"
    os.environ["ZUNEF_API_KEY"] = "team_key"
    config = resolve_llm_provider("strategic")
    assert config["base_url"] == "https://zunef.v2/api/v1"
    assert config["api_key_env"] == "ZUNEF_API_KEY"
```

### 2.2 test_topology_engine.py
```python
def test_vertical_chain_sequence():
    engine = TopologyEngine()
    chain = engine.get_vertical_chain()
    assert chain == ["swot", "plan", "cook", "test", "deploy", "audit"]

def test_commercial_chapter_routes_to_strategic():
    engine = TopologyEngine()
    level = engine.get_escalation("finance")  # Ch5
    assert level == EscalationLevel.STRATEGIC
```

### 2.3 test_jidoka_patterns.py
```python
def test_breaking_test_pattern_triggers_auto_fix():
    jidoka = JidokaMonitor()
    error = "BREAKING: snapshot test failed"
    pattern = jidoka.match_pattern(error)
    assert pattern.name == "breaking_test"
    assert pattern.auto_fix == "npm test -- --updateSnapshot"
```

## 3. Integration Tests

### 3.1 Dispatcher + Topology
```python
def test_full_vertical_dispatch():
    dispatcher = BinhPhapDispatcher()
    action = dispatcher.next_action()
    assert action["action"] == "execute"
    assert action["command"] == "swot"
    assert action["dimension"] == "vertical"
```

### 3.2 Command → LLM routing
```python
def test_cfo_command_routes_to_fable():
    config = dispatcher.get_llm_for_command("finance")
    assert config["model"] == "claude-fable-5"
    assert config["provider_name"] == "zunef-fable"  # or anthropic-fable
```

## 4. E2E Tests

### 4.1 Full Vertical Chain (simulated)
```
python3 -m src.main mk binh-phap --chain vertical
Expected output:
  [1/6] swot       -> OK (Fable 5)
  [2/6] plan       -> OK (Opus 4.8)
  [3/6] cook       -> OK (Opus 4.8)
  [4/6] test       -> OK (Opus 4.8)
  [5/6] deploy     -> OK (Opus 4.8)
  [6/6] audit      -> OK (Opus 4.8)
```

### 4.2 Jidoka Auto-fix
```
Simulate: BREAKING test failure
Expected: Jidoka auto-fix attempted -> success -> chain continues
Fallback: auto-fix fails -> escalation -> human approval
```

## 5. Load Test Spec

Run 100 vertical chains in sequence:
- Success rate >= 99%
- Average chain duration < 10 min
- Zero import errors
- Jidoka alerts <= 5 per run

## 6. Acceptance Checklist

| ID | Test | Command | Pass Criteria |
|----|------|---------|---------------|
| AC1 | Unit: escalation routing | pytest tests/test_binh_phap_escalation.py | All pass |
| AC2 | Unit: topology engine | pytest tests/test_topology_engine.py | All pass |
| AC3 | Unit: Jidoka patterns | pytest tests/test_jidoka_patterns.py | All pass |
| AC4 | Integration: dispatcher | pytest tests/test_dispatcher.py | All pass |
| AC5 | E2E: vertical chain | python3 -m src.main mk binh-phap --chain vertical | 6/6 OK |
| AC6 | Command: /mk:cfo | /mk:cfo "budget review" | Output + Fable route |
| AC7 | Command: /mk:cmo | /mk:cmo "campaign plan" | Output + Fable route |
| AC8 | Command: /mk:cso | /mk:cso "competitive intel" | Output + Fable route |
| AC9 | Auth: ZuneF fallback | Unset ZUNEF_API_KEY, rerun AC5 | Falls back to Anthropic |
| AC10 | Load: 100 chains | pytest tests/load/test_vertical_chain.py | 99% success |

## 7. Runbook

### 7.1 Quick Verify (5 min)
```bash
pytest tests/unit/test_binh_phap_escalation.py -v
pytest tests/unit/test_topology_engine.py -v
python3 -m src.main --help  # no errors
```

### 7.2 Full Verification (30 min)
```bash
pytest tests/ -v --tb=short
python3 -m src.main mk binh-phap --chain vertical
grep "fable" .mekong/jidoka-alerts.log  # verify routing
```

### 7.3 Rollback
If tests fail:
1. git revert HEAD~3 (last 3 commits)
2. python3 -m src.main --help (verify unbroken)
3. Investigate: cat docs/binh-phap-mapping/

## 8. Sign-off

| Role | Name | Sign | Date |
|------|------|------|------|
| Architect | sun-tzu | [ ] | |
| Reviewer | kongming | [ ] | |
| QA | | [ ] | |
