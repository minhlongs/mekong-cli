"""Founder Validate — /founder validate backend.

Customer discovery engine: hypothesis framework, interview scripts (Mom Test),
outreach messages, PMF survey (Sean Ellis), and interview analysis/synthesis.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Optional

logger = logging.getLogger(__name__)

InterviewVerdict = Literal[
    "PROBLEM CONFIRMED", "WEAK SIGNAL", "PIVOT NEEDED"
]
PMFLevel = Literal["STRONG", "MODERATE", "WEAK", "PIVOT"]


# ── Data Models ──────────────────────────────────────────────────────


@dataclass
class Assumption:
    """A riskiest assumption to validate."""

    id: str
    text: str
    risk_level: str  # "fatal" | "revenue" | "pivot"


@dataclass
class Hypothesis:
    """A falsifiable hypothesis to test."""

    id: str
    statement: str
    test_method: str
    success_metric: str


@dataclass
class ValidationFramework:
    """Output of Step 1 — hypothesis generation."""

    company_name: str
    idea: str
    assumptions: list[Assumption]
    hypotheses: list[Hypothesis]
    primary_persona: str
    secondary_persona: str
    avoid_persona: str


@dataclass
class InterviewNote:
    """Post-interview structured note."""

    interviewee: str
    pain_level: int  # 1-10
    budget_signal: str  # e.g. "$50/mo"
    current_solution: str
    key_quote: str
    referral_given: bool
    verdict: InterviewVerdict


@dataclass
class PMFResult:
    """Sean Ellis PMF survey analysis."""

    total_responses: int
    very_disappointed_pct: float
    somewhat_disappointed_pct: float
    not_disappointed_pct: float
    level: PMFLevel
    top_use_cases: list[str] = field(default_factory=list)
    positioning_language: list[str] = field(default_factory=list)


@dataclass
class ValidationAnalysis:
    """Synthesized analysis from interviews."""

    n_interviews: int
    common_pain: str
    common_solution: str
    avg_willingness_to_pay: str
    avg_pain_level: float
    problem_confirmed: bool
    key_quotes: list[dict[str, str]]
    positioning_insight: str
    icp_refinement: str
    pmf_signal: PMFLevel
    recommended_next: str


# ── Framework Generation ─────────────────────────────────────────────


def generate_framework(
    company_name: str, idea: str
) -> ValidationFramework:
    """Generate hypothesis framework from idea description."""
    if not idea or not idea.strip():
        raise ValueError("Idea description is required")

    assumptions = [
        Assumption(
            id="A1",
            text=f"Target customers actually experience the problem that {idea} solves",
            risk_level="fatal",
        ),
        Assumption(
            id="A2",
            text="Customers are willing to pay for a solution at our price point",
            risk_level="revenue",
        ),
        Assumption(
            id="A3",
            text="Current alternatives are insufficient — switching cost is acceptable",
            risk_level="pivot",
        ),
    ]

    hypotheses = [
        Hypothesis(
            id="H1",
            statement=f"At least 6/10 target users report pain level >= 7/10 for the problem {idea} solves",
            test_method="10 customer interviews using Mom Test method",
            success_metric="60% confirm pain >= 7/10",
        ),
        Hypothesis(
            id="H2",
            statement="Target users currently spend time/money on workarounds",
            test_method="Ask about current solutions and costs in interviews",
            success_metric="Average monthly spend on workarounds > $20",
        ),
    ]

    return ValidationFramework(
        company_name=company_name or "Unnamed",
        idea=idea,
        assumptions=assumptions,
        hypotheses=hypotheses,
        primary_persona="Decision-maker directly experiencing the pain",
        secondary_persona="Team member affected by the problem",
        avoid_persona="People who would give biased/polite answers (friends, family)",
    )


# ── Interview Kit ────────────────────────────────────────────────────


MOM_TEST_RULES = [
    "Ask about the PAST, not the future",
    "Never pitch. Never mention your solution.",
    "If they say 'great idea' — probe harder",
    "3 consecutive 'yes' answers = bad interviewer",
    "Write down exact words they use (for copy later)",
]

CORE_QUESTIONS = [
    {
        "q": "How have you tried solving this problem?",
        "probe": "Why wasn't that enough?",
    },
    {
        "q": "How much time/money do you spend on this per month?",
        "probe": "Is that a low or high estimate?",
    },
    {
        "q": "If this problem disappeared tomorrow, how would your life change?",
        "listen_for": "emotion, specific outcomes, dollar amounts",
    },
    {
        "q": "Who else in your org is affected by this?",
        "listen_for": "buyer vs user vs decision maker mapping",
    },
    {
        "q": "What have you searched for recently to find a solution?",
        "listen_for": "exact search terms = your SEO keywords",
    },
]


def generate_interview_script(
    problem_space: str, hypothesis_focus: str = "H1 + H2"
) -> dict:
    """Generate Mom Test-style interview script."""
    if not problem_space.strip():
        raise ValueError("Problem space description is required")

    return {
        "title": f"Interview Script — {hypothesis_focus}",
        "duration": "20-30 minutes",
        "goal": f"Validate/invalidate {hypothesis_focus}",
        "rules": MOM_TEST_RULES,
        "opening": (
            f"I'm researching {problem_space}. Can you tell me about "
            "the last time you dealt with this problem?"
        ),
        "core_questions": CORE_QUESTIONS,
        "closing_wtp": (
            "If there were a perfect solution, how much would you "
            "pay per month?"
        ),
        "closing_referral": (
            "Do you know anyone else dealing with a similar problem? "
            "Could I talk to them?"
        ),
        "post_interview_fields": [
            "pain_level (1-10)",
            "budget_signal ($X/mo)",
            "current_solution",
            "key_quote",
            "referral_given (Y/N)",
            "verdict: PROBLEM CONFIRMED / WEAK SIGNAL / PIVOT NEEDED",
        ],
    }


# ── Outreach Messages ───────────────────────────────────────────────


def generate_outreach_variants(
    problem_space: str, role: str = "founder"
) -> list[dict[str, str]]:
    """Generate 3 outreach message variants."""
    return [
        {
            "variant": "A",
            "strategy": "Problem-first (highest reply rate)",
            "message": (
                f"I'm researching {problem_space} and noticed you work as "
                f"{role}. I'm not selling anything — just want to hear about "
                f"your experience with this area. "
                "Would you have 20 minutes for a quick chat this week?"
            ),
        },
        {
            "variant": "B",
            "strategy": "Mutual connection",
            "message": (
                f"I was referred to you as someone who deeply understands "
                f"{problem_space}. I'm doing research for a project — "
                "could you spare 20 minutes?"
            ),
        },
        {
            "variant": "C",
            "strategy": "Content hook",
            "message": (
                f"I recently read your thoughts on {problem_space} — "
                f"very insightful. I'm researching this area and would love "
                "to hear your perspective. Could we chat for 20 minutes?"
            ),
        },
    ]


# ── PMF Survey ───────────────────────────────────────────────────────


PMF_QUESTIONS = [
    {
        "id": "Q1",
        "text": "How would you feel if you could no longer use {product}?",
        "options": [
            "Very disappointed",
            "Somewhat disappointed",
            "Not disappointed",
            "N/A — I no longer use it",
        ],
    },
    {
        "id": "Q2",
        "text": "What type of people would most benefit from {product}?",
        "type": "open_text",
    },
    {
        "id": "Q3",
        "text": "What is the main benefit you receive from {product}?",
        "type": "open_text",
    },
    {
        "id": "Q4",
        "text": "How can we improve {product} for you?",
        "type": "open_text",
    },
]

PMF_THRESHOLD_STRONG = 40.0
PMF_THRESHOLD_MODERATE = 25.0


def generate_pmf_survey(product_name: str) -> dict:
    """Generate Sean Ellis PMF survey template."""
    questions = []
    for q in PMF_QUESTIONS:
        rendered = {**q, "text": q["text"].format(product=product_name)}
        questions.append(rendered)

    return {
        "title": f"PMF Survey — {product_name}",
        "method": "Sean Ellis",
        "questions": questions,
        "threshold_info": {
            "strong": f">= {PMF_THRESHOLD_STRONG}% very disappointed",
            "moderate": f"{PMF_THRESHOLD_MODERATE}-{PMF_THRESHOLD_STRONG}% very disappointed",
            "weak": f"< {PMF_THRESHOLD_MODERATE}% very disappointed",
        },
        "distribution": "Send to first 50+ users who used product >= 2 times",
    }


def analyze_pmf_responses(
    responses: list[dict],
) -> PMFResult:
    """Analyze PMF survey responses and determine PMF level."""
    if not responses:
        raise ValueError("No responses to analyze")

    total = len(responses)
    very = sum(1 for r in responses if r.get("q1") == "Very disappointed")
    somewhat = sum(
        1 for r in responses if r.get("q1") == "Somewhat disappointed"
    )
    not_d = sum(
        1 for r in responses if r.get("q1") == "Not disappointed"
    )

    very_pct = (very / total) * 100
    somewhat_pct = (somewhat / total) * 100
    not_pct = (not_d / total) * 100

    if very_pct >= PMF_THRESHOLD_STRONG:
        level: PMFLevel = "STRONG"
    elif very_pct >= PMF_THRESHOLD_MODERATE:
        level = "MODERATE"
    elif very_pct >= 10:
        level = "WEAK"
    else:
        level = "PIVOT"

    # Extract use cases from Q2 open text
    use_cases = [
        r["q2"] for r in responses if r.get("q2") and r["q2"].strip()
    ]

    return PMFResult(
        total_responses=total,
        very_disappointed_pct=round(very_pct, 1),
        somewhat_disappointed_pct=round(somewhat_pct, 1),
        not_disappointed_pct=round(not_pct, 1),
        level=level,
        top_use_cases=use_cases[:5],
    )


# ── Interview Analysis ───────────────────────────────────────────────


def analyze_interviews(
    notes: list[InterviewNote],
) -> ValidationAnalysis:
    """Synthesize findings from multiple interview notes."""
    if not notes:
        raise ValueError("No interview notes to analyze")

    n = len(notes)
    avg_pain = sum(note.pain_level for note in notes) / n
    confirmed = sum(
        1 for note in notes if note.verdict == "PROBLEM CONFIRMED"
    )

    # Most common current solution
    solutions = [note.current_solution for note in notes if note.current_solution]
    common_solution = max(set(solutions), key=solutions.count) if solutions else "None identified"

    # Key quotes
    key_quotes = [
        {"quote": note.key_quote, "interviewee": note.interviewee}
        for note in notes
        if note.key_quote
    ]

    # Budget signals
    budgets = [note.budget_signal for note in notes if note.budget_signal]
    avg_budget = budgets[0] if len(budgets) == 1 else f"{budgets[0]} - {budgets[-1]}" if budgets else "Unknown"

    # Referral rate
    referral_rate = sum(1 for n in notes if n.referral_given) / len(notes) * 100

    # Determine PMF signal
    if avg_pain >= 8 and confirmed / n >= 0.7:
        signal: PMFLevel = "STRONG"
        next_step = "Build MVP and get first paying customer"
    elif avg_pain >= 6 and confirmed / n >= 0.5:
        signal = "MODERATE"
        next_step = "Refine positioning and do 5 more interviews"
    elif avg_pain >= 4:
        signal = "WEAK"
        next_step = "Pivot angle or re-examine ICP"
    else:
        signal = "PIVOT"
        next_step = "Major pivot needed — rethink the problem"

    return ValidationAnalysis(
        n_interviews=n,
        common_pain=f"Pain level avg {avg_pain:.1f}/10, {confirmed}/{n} confirmed",
        common_solution=common_solution,
        avg_willingness_to_pay=avg_budget,
        avg_pain_level=round(avg_pain, 1),
        problem_confirmed=confirmed / n >= 0.5,
        key_quotes=key_quotes[:5],
        positioning_insight=(
            f"Customers describe pain at {avg_pain:.1f}/10, "
            f"referral rate {referral_rate:.0f}%"
        ),
        icp_refinement=f"Based on {n} interviews, focus on personas with pain >= 7",
        pmf_signal=signal,
        recommended_next=next_step,
    )


# ── File I/O ─────────────────────────────────────────────────────────


def save_validation_kit(
    base_dir: str,
    framework: ValidationFramework,
    script: dict,
    outreach: list[dict],
    pmf_survey: Optional[dict] = None,
) -> list[str]:
    """Save all validation artifacts to .mekong/validate/."""
    validate_dir = Path(base_dir) / ".mekong" / "validate"
    validate_dir.mkdir(parents=True, exist_ok=True)
    saved: list[str] = []

    # Hypothesis framework
    fw_path = validate_dir / "hypothesis-framework.json"
    fw_path.write_text(json.dumps(asdict(framework), indent=2, ensure_ascii=False))
    saved.append(str(fw_path))

    # Interview script
    script_path = validate_dir / "interview-script.json"
    script_path.write_text(json.dumps(script, indent=2, ensure_ascii=False))
    saved.append(str(script_path))

    # Outreach messages
    outreach_path = validate_dir / "outreach-messages.json"
    outreach_path.write_text(json.dumps(outreach, indent=2, ensure_ascii=False))
    saved.append(str(outreach_path))

    # PMF survey (optional)
    if pmf_survey:
        pmf_path = validate_dir / "pmf-survey.json"
        pmf_path.write_text(json.dumps(pmf_survey, indent=2, ensure_ascii=False))
        saved.append(str(pmf_path))

    logger.info("Saved %d validation files to %s", len(saved), validate_dir)
    return saved


def save_analysis(
    base_dir: str,
    analysis: ValidationAnalysis,
) -> str:
    """Save interview analysis to .mekong/validate/."""
    validate_dir = Path(base_dir) / ".mekong" / "validate"
    validate_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d")
    path = validate_dir / f"analysis-{ts}.json"
    path.write_text(json.dumps(asdict(analysis), indent=2, ensure_ascii=False))
    return str(path)
