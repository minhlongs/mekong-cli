"""Tests for src/core/founder_hire.py."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.core.founder_hire import (
    define_role,
    generate_contractor_brief,
    generate_interview_kit,
    generate_jd,
    generate_posting_plan,
    save_hiring_kit,
    should_hire_human,
)


class TestHiringDecision(unittest.TestCase):
    def test_agent_always_agent(self):
        result = should_hire_human(100000, "agent")
        self.assertEqual(result["decision"], "AGENT")

    def test_low_mrr_fulltime_redirects(self):
        result = should_hire_human(5000, "fulltime")
        self.assertEqual(result["decision"], "CONTRACTOR")

    def test_high_mrr_fulltime_ok(self):
        result = should_hire_human(15000, "fulltime")
        self.assertEqual(result["decision"], "PROCEED")

    def test_contractor_always_ok(self):
        result = should_hire_human(1000, "contractor")
        self.assertEqual(result["decision"], "PROCEED")


class TestRoleDefinition(unittest.TestCase):
    def test_basic(self):
        role = define_role("Frontend Developer", "contractor", "mid", "React app")
        self.assertEqual(role.title, "Frontend Developer")
        self.assertEqual(role.role_type, "contractor")
        self.assertGreater(len(role.must_have), 0)

    def test_empty_title_raises(self):
        with self.assertRaises(ValueError):
            define_role("", "contractor", "mid")

    def test_90_day_milestones(self):
        role = define_role("Backend Engineer")
        self.assertIn("30", role.first_30_days)
        self.assertIn("pipeline", role.first_60_days.lower())


class TestJD(unittest.TestCase):
    def test_generate(self):
        role = define_role("Product Manager")
        jd = generate_jd(role, "Acme Inc", "$5K MRR")
        self.assertIn("Acme Inc", jd.about_company)
        self.assertIn("$5K MRR", jd.hook)
        self.assertGreater(len(jd.responsibilities), 0)

    def test_fulltime_equity(self):
        role = define_role("CTO", "fulltime", "senior")
        jd = generate_jd(role)
        self.assertIn("Discussed", jd.equity)

    def test_contractor_no_equity(self):
        role = define_role("Designer", "contractor", "mid")
        jd = generate_jd(role)
        self.assertEqual(jd.equity, "None")


class TestInterviewKit(unittest.TestCase):
    def test_developer_role(self):
        role = define_role("Software Developer")
        kit = generate_interview_kit(role)
        self.assertEqual(len(kit.screening_questions), 4)
        self.assertEqual(kit.work_sample.role_type, "developer")
        self.assertGreater(len(kit.deep_dive_questions), 0)

    def test_marketer_role(self):
        role = define_role("Content Marketer")
        kit = generate_interview_kit(role)
        self.assertEqual(kit.work_sample.role_type, "marketer")

    def test_ops_role(self):
        role = define_role("Operations Manager")
        kit = generate_interview_kit(role)
        self.assertEqual(kit.work_sample.role_type, "ops")

    def test_rubric(self):
        role = define_role("Engineer")
        kit = generate_interview_kit(role)
        self.assertEqual(len(kit.work_sample.rubric), 4)
        self.assertEqual(kit.work_sample.pass_threshold, 8)

    def test_reference_questions(self):
        role = define_role("Manager")
        kit = generate_interview_kit(role)
        self.assertEqual(len(kit.reference_check_questions), 2)


class TestContractorBrief(unittest.TestCase):
    def test_basic(self):
        brief = generate_contractor_brief("Designer", 4, 300)
        self.assertEqual(brief.total_budget, 6000.0)
        self.assertEqual(brief.duration_weeks, 4)
        self.assertGreater(len(brief.deliverables), 0)

    def test_custom_deliverables(self):
        brief = generate_contractor_brief("Dev", 2, 500, ["API", "Tests", "Docs"])
        self.assertEqual(len(brief.deliverables), 3)

    def test_payment_terms(self):
        brief = generate_contractor_brief("Writer", 1, 200)
        self.assertIn("50%", brief.payment_terms)


class TestPostingPlan(unittest.TestCase):
    def test_channels(self):
        plan = generate_posting_plan()
        self.assertGreater(len(plan.free_channels), 0)
        self.assertGreater(len(plan.paid_channels), 0)
        self.assertGreater(len(plan.sea_channels), 0)


class TestSaveHiringKit(unittest.TestCase):
    def test_save_basic(self):
        with TemporaryDirectory() as tmpdir:
            role = define_role("Developer")
            jd = generate_jd(role)
            kit = generate_interview_kit(role)
            saved = save_hiring_kit(tmpdir, role, jd, kit)
            self.assertEqual(len(saved), 3)  # jd + interview-kit + posting-plan
            for f in saved:
                self.assertTrue(Path(f).exists())

    def test_save_with_contractor(self):
        with TemporaryDirectory() as tmpdir:
            role = define_role("Designer", "contractor")
            jd = generate_jd(role)
            kit = generate_interview_kit(role)
            brief = generate_contractor_brief("Designer")
            saved = save_hiring_kit(tmpdir, role, jd, kit, brief)
            self.assertEqual(len(saved), 4)


if __name__ == "__main__":
    unittest.main()
