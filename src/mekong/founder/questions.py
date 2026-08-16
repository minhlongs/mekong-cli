# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Question sets for founder genome assessment.

Contains structured question definitions for:

- TIPI-10 (Ten-Item Personality Inventory, Gosling et al. 2003)
- Schwartz Values Inventory (10 value dimensions)
- Founder Fear Assessment (5 entries)
- Risk Self-Assessment (5 dimensions)
- Cognitive Bias Screening (10 yes/no questions)
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# TIPI-10 — Ten-Item Personality Inventory
# ---------------------------------------------------------------------------

TIPI_QUESTIONS: list[dict[str, Any]] = [
    {
        "id": "tipi_01",
        "text": "I see myself as extraverted, enthusiastic.",
        "type": "likert_7",
        "options": [
            {"value": 1, "label": "Disagree strongly"},
            {"value": 2, "label": "Disagree moderately"},
            {"value": 3, "label": "Disagree a little"},
            {"value": 4, "label": "Neutral"},
            {"value": 5, "label": "Agree a little"},
            {"value": 6, "label": "Agree moderately"},
            {"value": 7, "label": "Agree strongly"},
        ],
        "dimension": "extraversion",
        "reverse_scored": False,
    },
    {
        "id": "tipi_02",
        "text": "I see myself as critical, quarrelsome.",
        "type": "likert_7",
        "options": [
            {"value": 1, "label": "Disagree strongly"},
            {"value": 2, "label": "Disagree moderately"},
            {"value": 3, "label": "Disagree a little"},
            {"value": 4, "label": "Neutral"},
            {"value": 5, "label": "Agree a little"},
            {"value": 6, "label": "Agree moderately"},
            {"value": 7, "label": "Agree strongly"},
        ],
        "dimension": "agreeableness",
        "reverse_scored": True,
    },
    {
        "id": "tipi_03",
        "text": "I see myself as dependable, self-disciplined.",
        "type": "likert_7",
        "options": [
            {"value": 1, "label": "Disagree strongly"},
            {"value": 2, "label": "Disagree moderately"},
            {"value": 3, "label": "Disagree a little"},
            {"value": 4, "label": "Neutral"},
            {"value": 5, "label": "Agree a little"},
            {"value": 6, "label": "Agree moderately"},
            {"value": 7, "label": "Agree strongly"},
        ],
        "dimension": "conscientiousness",
        "reverse_scored": False,
    },
    {
        "id": "tipi_04",
        "text": "I see myself as anxious, easily upset.",
        "type": "likert_7",
        "options": [
            {"value": 1, "label": "Disagree strongly"},
            {"value": 2, "label": "Disagree moderately"},
            {"value": 3, "label": "Disagree a little"},
            {"value": 4, "label": "Neutral"},
            {"value": 5, "label": "Agree a little"},
            {"value": 6, "label": "Agree moderately"},
            {"value": 7, "label": "Agree strongly"},
        ],
        "dimension": "emotional_stability",
        "reverse_scored": True,
    },
    {
        "id": "tipi_05",
        "text": "I see myself as open to new experiences, complex.",
        "type": "likert_7",
        "options": [
            {"value": 1, "label": "Disagree strongly"},
            {"value": 2, "label": "Disagree moderately"},
            {"value": 3, "label": "Disagree a little"},
            {"value": 4, "label": "Neutral"},
            {"value": 5, "label": "Agree a little"},
            {"value": 6, "label": "Agree moderately"},
            {"value": 7, "label": "Agree strongly"},
        ],
        "dimension": "openness",
        "reverse_scored": False,
    },
    {
        "id": "tipi_06",
        "text": "I see myself as reserved, quiet.",
        "type": "likert_7",
        "options": [
            {"value": 1, "label": "Disagree strongly"},
            {"value": 2, "label": "Disagree moderately"},
            {"value": 3, "label": "Disagree a little"},
            {"value": 4, "label": "Neutral"},
            {"value": 5, "label": "Agree a little"},
            {"value": 6, "label": "Agree moderately"},
            {"value": 7, "label": "Agree strongly"},
        ],
        "dimension": "extraversion",
        "reverse_scored": True,
    },
    {
        "id": "tipi_07",
        "text": "I see myself as sympathetic, warm.",
        "type": "likert_7",
        "options": [
            {"value": 1, "label": "Disagree strongly"},
            {"value": 2, "label": "Disagree moderately"},
            {"value": 3, "label": "Disagree a little"},
            {"value": 4, "label": "Neutral"},
            {"value": 5, "label": "Agree a little"},
            {"value": 6, "label": "Agree moderately"},
            {"value": 7, "label": "Agree strongly"},
        ],
        "dimension": "agreeableness",
        "reverse_scored": False,
    },
    {
        "id": "tipi_08",
        "text": "I see myself as disorganized, careless.",
        "type": "likert_7",
        "options": [
            {"value": 1, "label": "Disagree strongly"},
            {"value": 2, "label": "Disagree moderately"},
            {"value": 3, "label": "Disagree a little"},
            {"value": 4, "label": "Neutral"},
            {"value": 5, "label": "Agree a little"},
            {"value": 6, "label": "Agree moderately"},
            {"value": 7, "label": "Agree strongly"},
        ],
        "dimension": "conscientiousness",
        "reverse_scored": True,
    },
    {
        "id": "tipi_09",
        "text": "I see myself as calm, emotionally stable.",
        "type": "likert_7",
        "options": [
            {"value": 1, "label": "Disagree strongly"},
            {"value": 2, "label": "Disagree moderately"},
            {"value": 3, "label": "Disagree a little"},
            {"value": 4, "label": "Neutral"},
            {"value": 5, "label": "Agree a little"},
            {"value": 6, "label": "Agree moderately"},
            {"value": 7, "label": "Agree strongly"},
        ],
        "dimension": "emotional_stability",
        "reverse_scored": False,
    },
    {
        "id": "tipi_10",
        "text": "I see myself as conventional, uncreative.",
        "type": "likert_7",
        "options": [
            {"value": 1, "label": "Disagree strongly"},
            {"value": 2, "label": "Disagree moderately"},
            {"value": 3, "label": "Disagree a little"},
            {"value": 4, "label": "Neutral"},
            {"value": 5, "label": "Agree a little"},
            {"value": 6, "label": "Agree moderately"},
            {"value": 7, "label": "Agree strongly"},
        ],
        "dimension": "openness",
        "reverse_scored": True,
    },
]

# ---------------------------------------------------------------------------
# Schwartz Values Inventory — 10 value dimensions
# ---------------------------------------------------------------------------

SCHWARTZ_VALUES: list[dict[str, str]] = [
    {"id": "self_direction", "label": "Self-Direction", "description": "Independent thought and action; choosing, creating, exploring."},
    {"id": "stimulation", "label": "Stimulation", "description": "Excitement, novelty, and challenge in life."},
    {"id": "hedonism", "label": "Hedonism", "description": "Pleasure and sensuous gratification for oneself."},
    {"id": "achievement", "label": "Achievement", "description": "Personal success through demonstrating competence according to social standards."},
    {"id": "power", "label": "Power", "description": "Social status and prestige, control or dominance over people and resources."},
    {"id": "security", "label": "Security", "description": "Safety, harmony, and stability of society, relationships, and self."},
    {"id": "conformity", "label": "Conformity", "description": "Restraint of actions, inclinations, and impulses likely to upset or harm others."},
    {"id": "tradition", "label": "Tradition", "description": "Respect, commitment, and acceptance of the customs and ideas that traditional culture or religion provide."},
    {"id": "benevolence", "label": "Benevolence", "description": "Preserving and enhancing the welfare of those with whom one is in frequent personal contact."},
    {"id": "universalism", "label": "Universalism", "description": "Understanding, appreciation, tolerance, and protection for the welfare of all people and nature."},
]

# ---------------------------------------------------------------------------
# Founder Fear Assessment — 5 entries
# ---------------------------------------------------------------------------

FEAR_FIELDS: list[str] = ["trigger", "predicted_behavior", "mitigation"]

FEAR_QUESTIONS: list[dict[str, Any]] = [
    {
        "id": "fear_01",
        "text": "What situation as a founder most triggers your anxiety or fear?",
        "type": "short_text",
        "field": "trigger",
        "dimension": "fear",
    },
    {
        "id": "fear_02",
        "text": "When that trigger appears, what behavior do you typically predict from yourself?",
        "type": "short_text",
        "field": "predicted_behavior",
        "dimension": "fear",
    },
    {
        "id": "fear_03",
        "text": "What mitigation strategy would you apply to reduce the impact of this fear?",
        "type": "short_text",
        "field": "mitigation",
        "dimension": "fear",
    },
    {
        "id": "fear_04",
        "text": "Describe a second situation that triggers anxiety as a founder.",
        "type": "short_text",
        "field": "trigger",
        "dimension": "fear",
    },
    {
        "id": "fear_05",
        "text": "For the second trigger, what behavior do you predict?",
        "type": "short_text",
        "field": "predicted_behavior",
        "dimension": "fear",
    },
    {
        "id": "fear_06",
        "text": "For the second trigger, what is your mitigation strategy?",
        "type": "short_text",
        "field": "mitigation",
        "dimension": "fear",
    },
    {
        "id": "fear_07",
        "text": "Describe a third situation that triggers anxiety as a founder.",
        "type": "short_text",
        "field": "trigger",
        "dimension": "fear",
    },
    {
        "id": "fear_08",
        "text": "For the third trigger, what behavior do you predict?",
        "type": "short_text",
        "field": "predicted_behavior",
        "dimension": "fear",
    },
    {
        "id": "fear_09",
        "text": "For the third trigger, what is your mitigation strategy?",
        "type": "short_text",
        "field": "mitigation",
        "dimension": "fear",
    },
    {
        "id": "fear_10",
        "text": "Describe a fourth situation that triggers anxiety as a founder.",
        "type": "short_text",
        "field": "trigger",
        "dimension": "fear",
    },
    {
        "id": "fear_11",
        "text": "For the fourth trigger, what behavior do you predict?",
        "type": "short_text",
        "field": "predicted_behavior",
        "dimension": "fear",
    },
    {
        "id": "fear_12",
        "text": "For the fourth trigger, what is your mitigation strategy?",
        "type": "short_text",
        "field": "mitigation",
        "dimension": "fear",
    },
    {
        "id": "fear_13",
        "text": "Describe a fifth situation that triggers anxiety as a founder.",
        "type": "short_text",
        "field": "trigger",
        "dimension": "fear",
    },
    {
        "id": "fear_14",
        "text": "For the fifth trigger, what behavior do you predict?",
        "type": "short_text",
        "field": "predicted_behavior",
        "dimension": "fear",
    },
    {
        "id": "fear_15",
        "text": "For the fifth trigger, what is your mitigation strategy?",
        "type": "short_text",
        "field": "mitigation",
        "dimension": "fear",
    },
]

# ---------------------------------------------------------------------------
# Risk Self-Assessment — 5 dimensions
# ---------------------------------------------------------------------------

RISK_DIMENSIONS: list[str] = [
    "financial",
    "operational",
    "reputational",
    "compliance",
    "technical",
]

RISK_QUESTIONS: list[dict[str, Any]] = [
    {
        "id": "risk_financial",
        "text": "How comfortable are you taking financial risks with company capital?",
        "type": "likert_10",
        "options": [
            {"value": 1, "label": "Extremely risk-averse"},
            {"value": 2, "label": ""},
            {"value": 3, "label": ""},
            {"value": 4, "label": ""},
            {"value": 5, "label": "Moderate"},
            {"value": 6, "label": ""},
            {"value": 7, "label": ""},
            {"value": 8, "label": ""},
            {"value": 9, "label": ""},
            {"value": 10, "label": "Extremely risk-seeking"},
        ],
        "dimension": "financial",
    },
    {
        "id": "risk_operational",
        "text": "How much operational uncertainty are you willing to accept?",
        "type": "likert_10",
        "options": [
            {"value": 1, "label": "Extremely risk-averse"},
            {"value": 2, "label": ""},
            {"value": 3, "label": ""},
            {"value": 4, "label": ""},
            {"value": 5, "label": "Moderate"},
            {"value": 6, "label": ""},
            {"value": 7, "label": ""},
            {"value": 8, "label": ""},
            {"value": 9, "label": ""},
            {"value": 10, "label": "Extremely risk-seeking"},
        ],
        "dimension": "operational",
    },
    {
        "id": "risk_reputational",
        "text": "How willing are you to risk public reputation for strategic gains?",
        "type": "likert_10",
        "options": [
            {"value": 1, "label": "Extremely risk-averse"},
            {"value": 2, "label": ""},
            {"value": 3, "label": ""},
            {"value": 4, "label": ""},
            {"value": 5, "label": "Moderate"},
            {"value": 6, "label": ""},
            {"value": 7, "label": ""},
            {"value": 8, "label": ""},
            {"value": 9, "label": ""},
            {"value": 10, "label": "Extremely risk-seeking"},
        ],
        "dimension": "reputational",
    },
    {
        "id": "risk_compliance",
        "text": "How comfortable are you operating in regulatory grey areas?",
        "type": "likert_10",
        "options": [
            {"value": 1, "label": "Extremely risk-averse"},
            {"value": 2, "label": ""},
            {"value": 3, "label": ""},
            {"value": 4, "label": ""},
            {"value": 5, "label": "Moderate"},
            {"value": 6, "label": ""},
            {"value": 7, "label": ""},
            {"value": 8, "label": ""},
            {"value": 9, "label": ""},
            {"value": 10, "label": "Extremely risk-seeking"},
        ],
        "dimension": "compliance",
    },
    {
        "id": "risk_technical",
        "text": "How much technical debt or unproven technology are you willing to adopt?",
        "type": "likert_10",
        "options": [
            {"value": 1, "label": "Extremely risk-averse"},
            {"value": 2, "label": ""},
            {"value": 3, "label": ""},
            {"value": 4, "label": ""},
            {"value": 5, "label": "Moderate"},
            {"value": 6, "label": ""},
            {"value": 7, "label": ""},
            {"value": 8, "label": ""},
            {"value": 9, "label": ""},
            {"value": 10, "label": "Extremely risk-seeking"},
        ],
        "dimension": "technical",
    },
]

# ---------------------------------------------------------------------------
# Cognitive Bias Screening — 10 yes/no questions
# ---------------------------------------------------------------------------

BIAS_QUESTIONS: list[dict[str, Any]] = [
    {
        "id": "bias_confirmation",
        "text": "Do you find yourself seeking evidence that confirms your existing beliefs more than evidence that challenges them?",
        "type": "yes_no",
        "options": [
            {"value": True, "label": "Yes"},
            {"value": False, "label": "No"},
        ],
        "dimension": "confirmation_bias",
        "bias_label": "Confirmation Bias",
    },
    {
        "id": "bias_overconfidence",
        "text": "Do you consistently rate your abilities higher than objective measures suggest?",
        "type": "yes_no",
        "options": [
            {"value": True, "label": "Yes"},
            {"value": False, "label": "No"},
        ],
        "dimension": "overconfidence",
        "bias_label": "Overconfidence Bias",
    },
    {
        "id": "bias_sunk_cost",
        "text": "Do you continue investing in failing projects because of what you have already put in?",
        "type": "yes_no",
        "options": [
            {"value": True, "label": "Yes"},
            {"value": False, "label": "No"},
        ],
        "dimension": "sunk_cost_fallacy",
        "bias_label": "Sunk Cost Fallacy",
    },
    {
        "id": "bias_planning",
        "text": "Do your projects consistently take longer and cost more than you initially estimated?",
        "type": "yes_no",
        "options": [
            {"value": True, "label": "Yes"},
            {"value": False, "label": "No"},
        ],
        "dimension": "planning_fallacy",
        "bias_label": "Planning Fallacy",
    },
    {
        "id": "bias_self_serving",
        "text": "Do you attribute successes to your own abilities and failures to external factors?",
        "type": "yes_no",
        "options": [
            {"value": True, "label": "Yes"},
            {"value": False, "label": "No"},
        ],
        "dimension": "self_serving_bias",
        "bias_label": "Self-Serving Bias",
    },
    {
        "id": "bias_anchoring",
        "text": "Do you rely heavily on the first piece of information you receive when making decisions?",
        "type": "yes_no",
        "options": [
            {"value": True, "label": "Yes"},
            {"value": False, "label": "No"},
        ],
        "dimension": "anchoring",
        "bias_label": "Anchoring Bias",
    },
    {
        "id": "bias_availability",
        "text": "Do you judge the likelihood of events based on how easily examples come to mind?",
        "type": "yes_no",
        "options": [
            {"value": True, "label": "Yes"},
            {"value": False, "label": "No"},
        ],
        "dimension": "availability_heuristic",
        "bias_label": "Availability Heuristic",
    },
    {
        "id": "bias_framing",
        "text": "Does the way a choice is presented (as a gain vs. a loss) strongly influence your decision?",
        "type": "yes_no",
        "options": [
            {"value": True, "label": "Yes"},
            {"value": False, "label": "No"},
        ],
        "dimension": "framing_effect",
        "bias_label": "Framing Effect",
    },
    {
        "id": "bias_status_quo",
        "text": "Do you prefer keeping things as they are rather than making changes?",
        "type": "yes_no",
        "options": [
            {"value": True, "label": "Yes"},
            {"value": False, "label": "No"},
        ],
        "dimension": "status_quo_bias",
        "bias_label": "Status Quo Bias",
    },
    {
        "id": "bias_optimism",
        "text": "Do you believe positive outcomes are more likely to happen to you than to others?",
        "type": "yes_no",
        "options": [
            {"value": True, "label": "Yes"},
            {"value": False, "label": "No"},
        ],
        "dimension": "optimism_bias",
        "bias_label": "Optimism Bias",
    },
]
