"""Tests for src/core/founder_validate.py."""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.core.founder_validate import (
    InterviewNote,
    analyze_interviews,
    analyze_pmf_responses,
    generate_framework,
    generate_interview_script,
    generate_outreach_variants,
    generate_pmf_survey,
    save_analysis,
    save_validation_kit,
)


class TestGenerateFramework(unittest.TestCase):
    def test_basic(self):
        fw = generate_framework("TestCo", "AI-powered task manager")
        self.assertEqual(fw.company_name, "TestCo")
        self.assertEqual(len(fw.assumptions), 3)
        self.assertEqual(len(fw.hypotheses), 2)
        self.assertEqual(fw.assumptions[0].risk_level, "fatal")

    def test_empty_idea_raises(self):
        with self.assertRaises(ValueError):
            generate_framework("Co", "")

    def test_whitespace_idea_raises(self):
        with self.assertRaises(ValueError):
            generate_framework("Co", "   ")

    def test_no_company_name(self):
        fw = generate_framework("", "some idea")
        self.assertEqual(fw.company_name, "Unnamed")


class TestInterviewScript(unittest.TestCase):
    def test_basic(self):
        script = generate_interview_script("project management")
        self.assertIn("rules", script)
        self.assertEqual(len(script["rules"]), 5)
        self.assertEqual(len(script["core_questions"]), 5)
        self.assertIn("project management", script["opening"])

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            generate_interview_script("")

    def test_custom_hypothesis(self):
        script = generate_interview_script("billing", "H3")
        self.assertIn("H3", script["goal"])


class TestOutreach(unittest.TestCase):
    def test_three_variants(self):
        variants = generate_outreach_variants("DevOps automation")
        self.assertEqual(len(variants), 3)
        self.assertEqual(variants[0]["variant"], "A")
        self.assertEqual(variants[2]["variant"], "C")

    def test_contains_problem(self):
        variants = generate_outreach_variants("cloud costs")
        self.assertIn("cloud costs", variants[0]["message"])


class TestPMFSurvey(unittest.TestCase):
    def test_generate(self):
        survey = generate_pmf_survey("WidgetApp")
        self.assertEqual(len(survey["questions"]), 4)
        self.assertIn("WidgetApp", survey["questions"][0]["text"])

    def test_analyze_strong(self):
        responses = [
            {"q1": "Very disappointed", "q2": "developers"} for _ in range(5)
        ] + [{"q1": "Not disappointed", "q2": ""} for _ in range(3)]
        result = analyze_pmf_responses(responses)
        self.assertEqual(result.level, "STRONG")
        self.assertGreaterEqual(result.very_disappointed_pct, 40)

    def test_analyze_weak(self):
        responses = [
            {"q1": "Very disappointed", "q2": "ops"} for _ in range(1)
        ] + [{"q1": "Not disappointed", "q2": ""} for _ in range(8)]
        result = analyze_pmf_responses(responses)
        self.assertEqual(result.level, "WEAK")

    def test_analyze_empty_raises(self):
        with self.assertRaises(ValueError):
            analyze_pmf_responses([])

    def test_analyze_pivot(self):
        responses = [{"q1": "Not disappointed", "q2": ""} for _ in range(10)]
        result = analyze_pmf_responses(responses)
        self.assertEqual(result.level, "PIVOT")


class TestAnalyzeInterviews(unittest.TestCase):
    def _make_notes(self, n, pain=8, verdict="PROBLEM CONFIRMED"):
        return [
            InterviewNote(
                interviewee=f"Person {i}",
                pain_level=pain,
                budget_signal=f"${50 + i * 10}/mo",
                current_solution="Spreadsheets",
                key_quote=f"This problem costs us hours — person {i}",
                referral_given=i % 2 == 0,
                verdict=verdict,
            )
            for i in range(n)
        ]

    def test_strong_signal(self):
        notes = self._make_notes(5, pain=9)
        analysis = analyze_interviews(notes)
        self.assertEqual(analysis.pmf_signal, "STRONG")
        self.assertTrue(analysis.problem_confirmed)

    def test_weak_signal(self):
        notes = self._make_notes(5, pain=4, verdict="WEAK SIGNAL")
        analysis = analyze_interviews(notes)
        self.assertIn(analysis.pmf_signal, ("WEAK", "PIVOT"))
        self.assertFalse(analysis.problem_confirmed)

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            analyze_interviews([])

    def test_key_quotes(self):
        notes = self._make_notes(3)
        analysis = analyze_interviews(notes)
        self.assertGreater(len(analysis.key_quotes), 0)


class TestSaveFiles(unittest.TestCase):
    def test_save_validation_kit(self):
        with TemporaryDirectory() as tmpdir:
            fw = generate_framework("Co", "idea")
            script = generate_interview_script("area")
            outreach = generate_outreach_variants("area")
            pmf = generate_pmf_survey("Product")
            saved = save_validation_kit(tmpdir, fw, script, outreach, pmf)
            self.assertEqual(len(saved), 4)
            for f in saved:
                self.assertTrue(Path(f).exists())

    def test_save_without_pmf(self):
        with TemporaryDirectory() as tmpdir:
            fw = generate_framework("Co", "idea")
            script = generate_interview_script("area")
            outreach = generate_outreach_variants("area")
            saved = save_validation_kit(tmpdir, fw, script, outreach)
            self.assertEqual(len(saved), 3)

    def test_save_analysis(self):
        with TemporaryDirectory() as tmpdir:
            notes = [
                InterviewNote("A", 8, "$50/mo", "Excel", "quote", True, "PROBLEM CONFIRMED")
            ]
            analysis = analyze_interviews(notes)
            path = save_analysis(tmpdir, analysis)
            self.assertTrue(Path(path).exists())
            data = json.loads(Path(path).read_text())
            self.assertEqual(data["n_interviews"], 1)


if __name__ == "__main__":
    unittest.main()
