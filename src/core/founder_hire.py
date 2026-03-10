"""Founder Hire — /founder hire backend.

Hiring intelligence: role definition, JD generation, 3-stage interview pipeline
(screening, work sample, deep dive), contractor brief, and job posting plan.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)

RoleType = Literal["fulltime", "contractor", "agent"]
Level = Literal["junior", "mid", "senior"]


# ── Data Models ──────────────────────────────────────────────────────


@dataclass
class RoleDefinition:
    """Core role definition."""

    title: str
    role_type: RoleType
    level: Level
    mission: str  # 1-sentence success definition
    must_have: list[str]
    nice_to_have: list[str]
    anti_requirements: list[str]
    key_metrics: list[str]
    first_30_days: str
    first_60_days: str
    first_90_days: str


@dataclass
class JobDescription:
    """Generated job description."""

    role: RoleDefinition
    hook: str  # 2-3 sentence attention grabber
    about_company: str
    responsibilities: list[str]
    success_at_90_days: list[str]
    salary_range: str
    equity: str
    remote: str
    how_to_apply: str


@dataclass
class InterviewQuestion:
    """A structured interview question."""

    question: str
    listen_for: str
    red_flag: str = ""
    stage: str = "screening"  # screening | work_sample | deep_dive


@dataclass
class WorkSample:
    """Work sample test definition."""

    role_type: str  # developer | marketer | ops
    task: str
    time_limit: str
    evaluate: list[str]
    rubric: list[dict[str, str]]
    pass_threshold: int = 8  # out of 12


@dataclass
class InterviewKit:
    """Complete 3-stage interview pipeline."""

    screening_questions: list[InterviewQuestion]
    work_sample: WorkSample
    deep_dive_questions: list[InterviewQuestion]
    reference_check_questions: list[str]


@dataclass
class ContractorBrief:
    """Project brief for contractor engagement."""

    role_title: str
    duration_weeks: int
    day_rate: float
    total_budget: float
    deliverables: list[dict[str, str]]
    definition_of_done: list[str]
    communication: str
    payment_terms: str


@dataclass
class PostingPlan:
    """Where and when to post the job."""

    free_channels: list[dict[str, str]]
    paid_channels: list[dict[str, str]]
    sea_channels: list[dict[str, str]]


# ── Philosophy ───────────────────────────────────────────────────────

HIRING_DECISION_TREE = {
    "step_1": "Can this be an AI agent? → /company agent train (free)",
    "step_2": "Can this be a contractor? → /founder hire --type contractor",
    "step_3": "Only then: hire fulltime (last resort)",
    "rule": "For solo founder at <$10K MRR: ONLY agents + contractors",
}


def should_hire_human(mrr: float, role_type: RoleType) -> dict[str, str]:
    """Decision helper: should we hire a human or use an agent?"""
    if role_type == "agent":
        return {"decision": "AGENT", "reason": "Use /company agent train instead"}

    if mrr < 10000 and role_type == "fulltime":
        return {
            "decision": "CONTRACTOR",
            "reason": f"MRR ${mrr} < $10K — fulltime too expensive. Use contractor.",
        }

    return {"decision": "PROCEED", "reason": f"MRR ${mrr} supports {role_type} hire"}


# ── Role Definition ──────────────────────────────────────────────────


def define_role(
    title: str,
    role_type: RoleType = "contractor",
    level: Level = "mid",
    context: str = "",
) -> RoleDefinition:
    """Generate role definition from title and context."""
    if not title.strip():
        raise ValueError("Role title is required")

    return RoleDefinition(
        title=title,
        role_type=role_type,
        level=level,
        mission=f"Own {title.lower()} outcomes and deliver measurable results",
        must_have=[
            f"2+ years experience in {title.lower()} role",
            "Self-starter, comfortable with ambiguity",
            "Strong written communication",
        ],
        nice_to_have=[
            "Startup experience",
            "Remote work experience",
            f"Domain expertise in {context or 'relevant area'}",
        ],
        anti_requirements=[
            "Needs constant supervision",
            "Uncomfortable with fast-paced changes",
            "Prefers large-team structures",
        ],
        key_metrics=[
            "Deliverables completed on time",
            "Quality of output (peer review score)",
            "Communication responsiveness",
        ],
        first_30_days=f"Complete 30-day onboarding: understand codebase/product, deliver first {title.lower()} task",
        first_60_days=f"Own {title.lower()} pipeline, establish recurring processes",
        first_90_days="Measurable impact on key metric, propose improvements",
    )


# ── Job Description ──────────────────────────────────────────────────


def generate_jd(
    role: RoleDefinition,
    company_name: str = "",
    traction: str = "",
    salary_range: str = "",
) -> JobDescription:
    """Generate job description from role definition."""
    return JobDescription(
        role=role,
        hook=(
            f"We're building something ambitious with a tiny team. "
            f"You'd be the person who actually moves the needle on "
            f"{role.title.lower()}. {traction}"
        ),
        about_company=(
            f"{company_name or 'Our company'} is an early-stage startup. "
            f"We're honest about where we are: things break, fast movers thrive."
        ),
        responsibilities=[
            f"Own {role.title.lower()} end-to-end",
            f"First 30 days: {role.first_30_days}",
            "Collaborate async with AI agents and founder",
        ],
        success_at_90_days=[
            role.first_90_days,
            "Established repeatable processes",
        ],
        salary_range=salary_range or "Competitive, based on experience",
        equity="Discussed after initial period" if role.role_type == "fulltime" else "None",
        remote="Yes — fully remote, async-first",
        how_to_apply=(
            f"Email with subject '{role.title} — [Your Name]'. "
            "Include: 1 relevant work sample, 1 paragraph on why this role, "
            "link to portfolio/GitHub."
        ),
    )


# ── Interview Kit ────────────────────────────────────────────────────


def generate_interview_kit(role: RoleDefinition) -> InterviewKit:
    """Generate 3-stage interview pipeline."""
    screening = [
        InterviewQuestion(
            "Walk me through your last relevant project.",
            "specifics, ownership language ('I built' vs 'we tried')",
            "vague, no ownership",
            "screening",
        ),
        InterviewQuestion(
            "What's the hardest problem you've solved?",
            "clarity of thinking, depth",
            "can't articulate clearly",
            "screening",
        ),
        InterviewQuestion(
            "Why this role, why now?",
            "genuine interest, knows our product",
            "vague answer, doesn't know product",
            "screening",
        ),
        InterviewQuestion(
            f"Our range is {role.level}-level. Does that work?",
            "alignment on compensation",
            "mismatched expectations",
            "screening",
        ),
    ]

    # Work sample based on role
    if "developer" in role.title.lower() or "engineer" in role.title.lower():
        ws_type = "developer"
        ws_task = f"Small coding task related to {role.title}"
        ws_eval = ["code quality", "communication", "approach"]
    elif "market" in role.title.lower() or "content" in role.title.lower():
        ws_type = "marketer"
        ws_task = "Write a launch post targeting our ICP"
        ws_eval = ["voice match", "insight", "clarity"]
    else:
        ws_type = "ops"
        ws_task = f"Design a process for a recurring {role.title.lower()} task"
        ws_eval = ["clarity", "edge cases", "efficiency"]

    work_sample = WorkSample(
        role_type=ws_type,
        task=ws_task,
        time_limit="2-3 hours" if ws_type == "developer" else "1-2 hours",
        evaluate=ws_eval,
        rubric=[
            {"criterion": "Accomplishes core goal", "max_score": "3"},
            {"criterion": "Quality acceptable for shipping", "max_score": "3"},
            {"criterion": "Shows initiative beyond minimum", "max_score": "3"},
            {"criterion": "Communication clear throughout", "max_score": "3"},
        ],
    )

    deep_dive = [
        InterviewQuestion(
            f"Deep technical question about {role.title}",
            "can they go deep? know what they don't know?",
            stage="deep_dive",
        ),
        InterviewQuestion(
            "Tell me about a time you disagreed with your manager.",
            "intellectual honesty, constructive approach",
            "blaming others",
            "deep_dive",
        ),
        InterviewQuestion(
            "What would you have done differently at your last job?",
            "self-reflection, growth mindset",
            "'Nothing, it was great'",
            "deep_dive",
        ),
    ]

    ref_questions = [
        "On a scale 1-10, how likely would you rehire {name}? Why not a 10?",
        "What's the biggest area for growth for {name}?",
    ]

    return InterviewKit(
        screening_questions=screening,
        work_sample=work_sample,
        deep_dive_questions=deep_dive,
        reference_check_questions=ref_questions,
    )


# ── Contractor Brief ─────────────────────────────────────────────────


def generate_contractor_brief(
    role_title: str,
    duration_weeks: int = 4,
    day_rate: float = 300.0,
    deliverables: list[str] | None = None,
) -> ContractorBrief:
    """Generate contractor project brief."""
    total = day_rate * duration_weeks * 5  # 5 days/week

    default_deliverables = [
        {"deliverable": f"{role_title} task 1", "deadline": "Week 2"},
        {"deliverable": f"{role_title} task 2", "deadline": "Week 3"},
        {"deliverable": "Final handoff + documentation", "deadline": f"Week {duration_weeks}"},
    ]

    if deliverables:
        default_deliverables = [
            {"deliverable": d, "deadline": f"Week {i + 1}"}
            for i, d in enumerate(deliverables)
        ]

    return ContractorBrief(
        role_title=role_title,
        duration_weeks=duration_weeks,
        day_rate=day_rate,
        total_budget=total,
        deliverables=default_deliverables,
        definition_of_done=[
            "All deliverables completed and approved",
            "Documentation complete",
            "Knowledge transfer session done",
        ],
        communication="Async via Slack/Discord, 2 check-ins/week (30 min each)",
        payment_terms="50% upfront, 50% on completion",
    )


# ── Posting Plan ─────────────────────────────────────────────────────


def generate_posting_plan() -> PostingPlan:
    """Generate job posting channel plan."""
    return PostingPlan(
        free_channels=[
            {"channel": "Hacker News 'Who's hiring?' thread", "reach": "huge for tech"},
            {"channel": "Twitter/X post", "reach": "your network"},
            {"channel": "LinkedIn post", "reach": "professional network"},
            {"channel": "Relevant Slack/Discord communities", "reach": "targeted"},
        ],
        paid_channels=[
            {"channel": "RemoteOK.io", "cost": "$200-400", "duration": "30 days"},
            {"channel": "We Work Remotely", "cost": "$299", "duration": "30 days"},
            {"channel": "Contra", "cost": "revenue share", "duration": "ongoing"},
        ],
        sea_channels=[
            {"channel": "ITviec", "market": "Vietnam tech"},
            {"channel": "TopDev", "market": "Vietnam tech"},
            {"channel": "LinkedIn Vietnam groups", "market": "Vietnam"},
            {"channel": "Facebook: Vietnam Developer Community", "market": "Vietnam"},
        ],
    )


# ── File I/O ─────────────────────────────────────────────────────────


def save_hiring_kit(
    base_dir: str,
    role: RoleDefinition,
    jd: JobDescription,
    kit: InterviewKit,
    contractor_brief: ContractorBrief | None = None,
) -> list[str]:
    """Save complete hiring kit to .mekong/hire/{role}-{date}/."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d")
    slug = role.title.lower().replace(" ", "-")
    hire_dir = Path(base_dir) / ".mekong" / "hire" / f"{slug}-{ts}"
    hire_dir.mkdir(parents=True, exist_ok=True)
    saved: list[str] = []

    # JD
    path = hire_dir / "jd.json"
    jd_data = asdict(jd)
    path.write_text(json.dumps(jd_data, indent=2, ensure_ascii=False))
    saved.append(str(path))

    # Interview kit
    path = hire_dir / "interview-kit.json"
    path.write_text(json.dumps(asdict(kit), indent=2, ensure_ascii=False))
    saved.append(str(path))

    # Posting plan
    plan = generate_posting_plan()
    path = hire_dir / "posting-plan.json"
    path.write_text(json.dumps(asdict(plan), indent=2, ensure_ascii=False))
    saved.append(str(path))

    # Contractor brief (if applicable)
    if contractor_brief:
        path = hire_dir / "contractor-brief.json"
        path.write_text(json.dumps(asdict(contractor_brief), indent=2, ensure_ascii=False))
        saved.append(str(path))

    return saved
