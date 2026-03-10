"""Tests for company_init.py — /company init wizard backend."""

import json
import tempfile
from pathlib import Path

import pytest

from src.core.company_init import (
    CompanyConfig,
    validate_config,
    generate_config_files,
    write_config_files,
    seed_mcu_balance,
    init_company,
    AGENT_ROLES,
    PRODUCT_MAP,
    SCENARIO_MAP,
    BUDGET_MAP,
    LANGUAGE_MAP,
)
from src.core.mcu_gate import MCUGate


def _make_config(**overrides) -> CompanyConfig:
    defaults = {
        "company_name": "TestCorp",
        "product_type": "saas",
        "scenario": "hybrid",
        "budget_tier": "minimal",
        "primary_language": "vi",
    }
    defaults.update(overrides)
    return CompanyConfig(**defaults)


class TestValidateConfig:
    def test_valid_config(self):
        assert validate_config(_make_config()) == []

    def test_empty_company_name(self):
        errors = validate_config(_make_config(company_name=""))
        assert any("company_name" in e for e in errors)

    def test_invalid_product_type(self):
        errors = validate_config(_make_config(product_type="invalid"))
        assert any("product_type" in e for e in errors)

    def test_invalid_scenario(self):
        errors = validate_config(_make_config(scenario="cloud_only"))
        assert any("scenario" in e for e in errors)

    def test_invalid_budget(self):
        errors = validate_config(_make_config(budget_tier="ultra"))
        assert any("budget_tier" in e for e in errors)

    def test_invalid_language(self):
        errors = validate_config(_make_config(primary_language="jp"))
        assert any("primary_language" in e for e in errors)


class TestGenerateConfigFiles:
    def test_generates_12_files(self):
        files = generate_config_files(_make_config())
        assert len(files) == 12

    def test_company_json_content(self):
        cfg = _make_config(company_name="AcmeCo")
        files = generate_config_files(cfg)
        data = json.loads(files[".mekong/company.json"])
        assert data["company_name"] == "AcmeCo"
        assert data["product_type"] == "saas"
        assert data["version"] == "1.0"

    def test_openclaw_config_has_routing(self):
        files = generate_config_files(_make_config())
        data = json.loads(files[".openclaw/config.json"])
        assert "routing_rules" in data
        assert "cto" in data["routing_rules"]
        assert "fallback_chain" in data

    def test_agent_prompts_generated(self):
        cfg = _make_config(company_name="MyCorp", primary_language="en")
        files = generate_config_files(cfg)
        for role in AGENT_ROLES:
            key = f".mekong/agents/{role}.md"
            assert key in files, f"Missing agent file: {key}"
            assert "MyCorp" in files[key]
            assert "en" in files[key]

    def test_mcu_balance_json(self):
        files = generate_config_files(_make_config())
        data = json.loads(files[".mekong/mcu_balance.json"])
        assert data["balance"] == 100
        assert data["tier"] == "starter"

    def test_invalid_config_raises(self):
        with pytest.raises(ValueError, match="Invalid config"):
            generate_config_files(_make_config(company_name=""))

    def test_local_first_uses_ollama(self):
        cfg = _make_config(scenario="local_first")
        files = generate_config_files(cfg)
        data = json.loads(files[".openclaw/config.json"])
        coo_model = data["routing_rules"]["coo"]
        assert "ollama" in str(coo_model)

    def test_api_only_uses_cloud(self):
        cfg = _make_config(scenario="api_only")
        files = generate_config_files(cfg)
        data = json.loads(files[".openclaw/config.json"])
        coo_model = data["routing_rules"]["coo"]
        assert "ollama" not in str(coo_model)


class TestWriteConfigFiles:
    def test_writes_files_to_disk(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            files = {"test/a.json": '{"a": 1}', "test/b.md": "# Hello"}
            written = write_config_files(files, tmpdir)
            assert len(written) == 2
            assert (Path(tmpdir) / "test" / "a.json").exists()
            assert (Path(tmpdir) / "test" / "b.md").exists()

    def test_creates_nested_dirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            files = {"deep/nested/file.txt": "content"}
            write_config_files(files, tmpdir)
            assert (Path(tmpdir) / "deep" / "nested" / "file.txt").read_text() == "content"


class TestSeedMCUBalance:
    def test_seed_starter(self):
        amount = seed_mcu_balance("t1", "starter")
        assert amount == 100

    def test_seed_growth(self):
        amount = seed_mcu_balance("t1", "growth")
        assert amount == 500

    def test_seed_premium(self):
        amount = seed_mcu_balance("t1", "premium")
        assert amount == 2000

    def test_seed_with_mcu_gate(self):
        gate = MCUGate(":memory:")
        seed_mcu_balance("t1", "starter", mcu_gate=gate)
        balance = gate.get_balance("t1")
        assert balance["balance"] == 100

    def test_seed_unknown_tier_defaults(self):
        amount = seed_mcu_balance("t1", "unknown_tier")
        assert amount == 100


class TestInitCompany:
    def test_full_init(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = _make_config(company_name="InitTest")
            result = init_company(cfg, base_dir=tmpdir)
            assert result["company_name"] == "InitTest"
            assert result["files_created"] == 12
            assert result["mcu_seeded"] == 100
            assert (Path(tmpdir) / ".mekong" / "company.json").exists()

    def test_init_with_mcu_gate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            gate = MCUGate(":memory:")
            cfg = _make_config()
            init_company(cfg, base_dir=tmpdir, mcu_gate=gate, tenant_id="t1")
            balance = gate.get_balance("t1")
            assert balance["balance"] == 100

    def test_double_init_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = _make_config()
            init_company(cfg, base_dir=tmpdir)
            with pytest.raises(FileExistsError, match="already setup"):
                init_company(cfg, base_dir=tmpdir)


class TestMappingConstants:
    def test_product_map_keys(self):
        assert set(PRODUCT_MAP.keys()) == {"1", "2", "3", "4"}

    def test_scenario_map_keys(self):
        assert set(SCENARIO_MAP.keys()) == {"1", "2", "3", "4"}

    def test_budget_map_keys(self):
        assert set(BUDGET_MAP.keys()) == {"1", "2", "3", "4"}

    def test_language_map_keys(self):
        assert set(LANGUAGE_MAP.keys()) == {"1", "2", "3"}

    def test_8_agent_roles(self):
        assert len(AGENT_ROLES) == 8
        assert "cto" in AGENT_ROLES
        assert "data" in AGENT_ROLES
