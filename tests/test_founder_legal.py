"""Tests for src/core/founder_legal.py."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.core.founder_legal import (
    build_compliance_checklists,
    build_contract_templates,
    build_incorporation_checklist,
    build_ip_checklist,
    build_legal_kit,
    save_legal_kit,
)


class TestIncorporation(unittest.TestCase):
    def test_vietnam(self):
        checklist = build_incorporation_checklist("vietnam")
        self.assertEqual(checklist.jurisdiction, "vietnam")
        self.assertIn("TNHH", checklist.entity_type)
        self.assertGreater(len(checklist.items), 3)

    def test_us_delaware(self):
        checklist = build_incorporation_checklist("us_delaware")
        self.assertIn("C-Corp", checklist.entity_type)
        atlas = [i for i in checklist.items if "Atlas" in i.task]
        self.assertGreater(len(atlas), 0)

    def test_singapore(self):
        checklist = build_incorporation_checklist("singapore")
        self.assertIn("Pte Ltd", checklist.entity_type)

    def test_other(self):
        checklist = build_incorporation_checklist("other")
        self.assertIn("LLC", checklist.entity_type)

    def test_post_incorporation(self):
        checklist = build_incorporation_checklist("vietnam")
        self.assertGreater(len(checklist.post_incorporation), 0)
        ip_assign = [i for i in checklist.post_incorporation if "IP" in i.task]
        self.assertGreater(len(ip_assign), 0)


class TestIP(unittest.TestCase):
    def test_has_sections(self):
        ip = build_ip_checklist()
        self.assertGreater(len(ip.code_items), 0)
        self.assertGreater(len(ip.trademark_items), 0)
        self.assertGreater(len(ip.domain_items), 0)
        self.assertGreater(len(ip.trade_secret_items), 0)

    def test_code_items_priority(self):
        ip = build_ip_checklist()
        high = [i for i in ip.code_items if i.priority == "high"]
        self.assertGreater(len(high), 2)


class TestContracts(unittest.TestCase):
    def test_five_templates(self):
        contracts = build_contract_templates()
        self.assertEqual(len(contracts), 5)

    def test_types(self):
        contracts = build_contract_templates()
        types = {c.type for c in contracts}
        self.assertIn("tos", types)
        self.assertIn("privacy", types)
        self.assertIn("contractor", types)

    def test_sections_not_empty(self):
        contracts = build_contract_templates()
        for c in contracts:
            self.assertGreater(len(c.sections), 0)


class TestCompliance(unittest.TestCase):
    def test_has_gdpr(self):
        checklists = build_compliance_checklists()
        gdpr = [c for c in checklists if c.framework == "GDPR"]
        self.assertEqual(len(gdpr), 1)
        self.assertGreater(len(gdpr[0].items), 3)

    def test_has_pdpa(self):
        checklists = build_compliance_checklists()
        pdpa = [c for c in checklists if "PDPA" in c.framework]
        self.assertEqual(len(pdpa), 1)

    def test_general_security(self):
        checklists = build_compliance_checklists()
        general = [c for c in checklists if c.framework == "General Security"]
        self.assertEqual(len(general), 1)
        self.assertGreater(len(general[0].items), 3)

    def test_total_frameworks(self):
        checklists = build_compliance_checklists()
        self.assertGreaterEqual(len(checklists), 4)


class TestLegalKit(unittest.TestCase):
    def test_full_kit(self):
        kit = build_legal_kit("vietnam")
        self.assertEqual(kit.incorporation.jurisdiction, "vietnam")
        self.assertGreater(len(kit.contracts), 0)
        self.assertGreater(len(kit.compliance), 0)
        self.assertIn("STARTING POINTS", kit.disclaimer)

    def test_us_kit(self):
        kit = build_legal_kit("us_delaware")
        self.assertIn("C-Corp", kit.incorporation.entity_type)


class TestSaveLegalKit(unittest.TestCase):
    def test_save(self):
        with TemporaryDirectory() as tmpdir:
            kit = build_legal_kit("vietnam")
            saved = save_legal_kit(tmpdir, kit)
            # incorporation + ip + 5 contracts + compliance = 8
            self.assertGreaterEqual(len(saved), 7)
            for f in saved:
                self.assertTrue(Path(f).exists())

    def test_contracts_dir_created(self):
        with TemporaryDirectory() as tmpdir:
            kit = build_legal_kit("singapore")
            save_legal_kit(tmpdir, kit)
            contracts_dir = Path(tmpdir) / ".mekong" / "legal" / "contracts"
            self.assertTrue(contracts_dir.exists())
            self.assertGreater(len(list(contracts_dir.glob("*.json"))), 0)


if __name__ == "__main__":
    unittest.main()
