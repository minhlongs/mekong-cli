# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Executable operation contracts for Wave 5A C-Suite & Business Operations (L0–L3).

Registers twelve executable commands across four departments:

* ``ceo-command`` (L0 / ``company-blueprint``): ``idea``, ``goal``, ``governance``, ``binh-phap``
* ``quality-compliance`` (L2 / ``mvp-live``): ``csuite``
* ``sales-revenue`` (L3 / ``first-revenue``): ``zenpay``, ``revenue``, ``usage``, ``consulting``
* ``growth-marketing`` (L3 / ``repeatable-channel``): ``content``, ``copywriting``
* ``platform-operations`` (L2 / ``mvp-live``): ``vendor``

Every operation is bound to a real core engine plus a workspace-scoped SQLite
ledger; the irreversible ones require ``FOUNDER_CONFIRMATION`` before persisting
a state change.
"""

from __future__ import annotations

from src.core.promise.contracts import HandlerRef, OperationSpec, Postcondition

TEST_MODULE = "tests/test_promise_wave5_ops.py"

CEO_COMMAND_OPS: tuple[OperationSpec, ...] = (
    OperationSpec(
        op_id="idea.synthesize-blueprint",
        command="idea",
        subcommand="synthesize_blueprint",
        title="Tổng hợp bản kiến trúc dự án startup (Venture Blueprint Synthesis L0)",
        description=(
            "Synthesize a structured venture blueprint from problem, segment and monetization "
            "model, persisting it to workspace idea.db with viability scoring."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "venture_name": {"type": "string", "minLength": 2, "maxLength": 200},
                "problem_statement": {"type": "string", "minLength": 10, "maxLength": 600},
                "target_segment": {
                    "type": "string",
                    "default": "Vietnamese SMEs & One-Person Companies",
                },
                "monetization_model": {
                    "type": "string",
                    "enum": ["DUAL_RAIL_SAAS", "B2B_RETAINER", "USAGE_MCU", "MARKETPLACE"],
                    "default": "DUAL_RAIL_SAAS",
                },
            },
            "required": ["venture_name", "problem_statement"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_csuite_bizops_wave5:idea_synthesize_blueprint",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/idea.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "blueprint_id",
                        "venture_name",
                        "viability_score",
                        "readiness_tier",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "venture_name", "result_path": "venture_name"}),
            Postcondition("value_bounds", {"path": "viability_score", "min": 0, "max": 100}),
            Postcondition(
                "enum_member",
                {"path": "readiness_tier", "allowed": ["READY_FOR_CHARTER", "NEEDS_REFINEMENT"]},
            ),
            Postcondition(
                "record_persisted",
                {"table": "idea_blueprints", "id_path": "blueprint_id", "id_column": "blueprint_id"},
            ),
        ),
        sop_steps=("capture-problem-statement", "score-viability", "persist-idea-blueprint"),
        department_id="ceo-command",
        layer_id="L0",
        gate_id="company-blueprint",
        jurisdiction="GLOBAL",
        rule_version="Mekong Idea Blueprint Synthesis v1",
        output_contract={"evidence_type": "IDEA_BLUEPRINT_RECORD"},
        test_id=f"{TEST_MODULE}::test_idea_synthesize_blueprint_and_founder_gated_charter",
    ),
    OperationSpec(
        op_id="idea.approve-charter",
        command="idea",
        subcommand="approve_charter",
        title="Phê duyệt & đóng dấu Điều lệ hoạt động dự án (Founder Charter Ratification L0)",
        description=(
            "Ratify a venture charter with a SHA-256 commitment digest and initial capital, "
            "persisting the sealed charter to workspace idea.db after founder confirmation."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "venture_name": {"type": "string", "minLength": 2, "maxLength": 200},
                "initial_capital_vnd": {"type": "number", "minimum": 0, "maximum": 10_000_000_000_000},
                "strategic_pillar": {"type": "string", "default": "AI-Native One-Person Company OS"},
                "approved_by": {"type": "string", "default": "Founder"},
            },
            "required": ["venture_name", "initial_capital_vnd"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_csuite_bizops_wave5:idea_approve_charter",
        ),
        approval_policy="FOUNDER_CONFIRMATION",
        effects=(
            "WRITE:.mekong/workspaces/{workspace_id}/idea.db",
            "WRITE:.mekong/promise_evidence.db",
        ),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "charter_id",
                        "venture_name",
                        "initial_capital_vnd",
                        "charter_hash",
                        "status",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "venture_name", "result_path": "venture_name"}),
            Postcondition("value_bounds", {"path": "initial_capital_vnd", "min": 0, "max": 10_000_000_000_000}),
            Postcondition(
                "enum_member",
                {"path": "status", "allowed": ["CHARTER_APPROVED"]},
            ),
            Postcondition(
                "record_persisted",
                {"table": "idea_blueprints", "id_path": "charter_id", "id_column": "blueprint_id"},
            ),
        ),
        sop_steps=("verify-founder-authority", "hash-charter-commitment", "seal-charter"),
        department_id="ceo-command",
        layer_id="L0",
        gate_id="company-blueprint",
        jurisdiction="GLOBAL",
        rule_version="Mekong Founder Charter Ratification v1",
        output_contract={"evidence_type": "IDEA_CHARTER_SEAL"},
        test_id=f"{TEST_MODULE}::test_idea_synthesize_blueprint_and_founder_gated_charter",
    ),
    OperationSpec(
        op_id="goal.decompose-mission",
        command="goal",
        subcommand="decompose_mission",
        title="Phân rã mục tiêu chiến lược thành OKR (Mission Decomposition L0)",
        description=(
            "Decompose a quarterly strategic objective into measurable OKR key results with "
            "graduated milestones, persisting the draft to workspace goal.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "objective_title": {"type": "string", "minLength": 3, "maxLength": 240},
                "target_metric_name": {"type": "string", "minLength": 3, "maxLength": 120},
                "target_metric_value": {"type": "number", "exclusiveMinimum": 0},
                "quarter": {"type": "string", "default": "Q4/2026"},
                "owner_department": {"type": "string", "default": "ceo-command"},
            },
            "required": ["objective_title", "target_metric_name", "target_metric_value"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_csuite_bizops_wave5:goal_decompose_mission",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/goal.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "mission_id",
                        "objective_title",
                        "target_metric_value",
                        "key_results_count",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "objective_title", "result_path": "objective_title"}),
            Postcondition("value_bounds", {"path": "target_metric_value", "min": 0}),
            Postcondition("value_bounds", {"path": "key_results_count", "min": 3, "max": 3}),
            Postcondition(
                "enum_member",
                {"path": "lock_status", "allowed": ["DECOMPOSED_DRAFT"]},
            ),
            Postcondition(
                "record_persisted",
                {"table": "goal_missions", "id_path": "mission_id", "id_column": "mission_id"},
            ),
        ),
        sop_steps=("frame-objective", "grade-key-results", "persist-mission-draft"),
        department_id="ceo-command",
        layer_id="L0",
        gate_id="company-blueprint",
        jurisdiction="GLOBAL",
        rule_version="Mekong Goal Mission Decomposition v1",
        output_contract={"evidence_type": "GOAL_MISSION_RECORD"},
        test_id=f"{TEST_MODULE}::test_goal_decompose_mission_and_founder_locked_targets",
    ),
    OperationSpec(
        op_id="goal.lock-quarterly-targets",
        command="goal",
        subcommand="lock_quarterly_targets",
        title="Khóa cam kết mục tiêu quý (Immutable Quarterly Target Lock L0)",
        description=(
            "Lock immutable quarterly OKR targets with a SHA-256 commitment digest and "
            "MRR projection, persisting the locked commitment to workspace goal.db after "
            "founder confirmation."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "objective_title": {"type": "string", "minLength": 3, "maxLength": 240},
                "quarter": {"type": "string", "minLength": 4, "maxLength": 16},
                "target_mrr_usd": {"type": "number", "exclusiveMinimum": 0, "maximum": 10_000_000},
                "owner_department": {"type": "string", "default": "ceo-command"},
            },
            "required": ["objective_title", "quarter", "target_mrr_usd"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_csuite_bizops_wave5:goal_lock_quarterly_targets",
        ),
        approval_policy="FOUNDER_CONFIRMATION",
        effects=(
            "WRITE:.mekong/workspaces/{workspace_id}/goal.db",
            "WRITE:.mekong/promise_evidence.db",
        ),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "mission_id",
                        "objective_title",
                        "quarter",
                        "target_mrr_usd",
                        "commitment_hash",
                        "lock_status",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "quarter", "result_path": "quarter"}),
            Postcondition("value_bounds", {"path": "target_mrr_usd", "min": 0, "max": 10_000_000}),
            Postcondition(
                "enum_member",
                {"path": "lock_status", "allowed": ["LOCKED_COMMITTED"]},
            ),
            Postcondition(
                "record_persisted",
                {"table": "goal_missions", "id_path": "mission_id", "id_column": "mission_id"},
            ),
        ),
        sop_steps=("verify-founder-authority", "hash-quarterly-commitment", "lock-targets"),
        department_id="ceo-command",
        layer_id="L0",
        gate_id="company-blueprint",
        jurisdiction="GLOBAL",
        rule_version="Mekong Quarterly Commitment Lock v1",
        output_contract={"evidence_type": "GOAL_COMMITMENT_SEAL"},
        test_id=f"{TEST_MODULE}::test_goal_decompose_mission_and_founder_locked_targets",
    ),
    OperationSpec(
        op_id="governance.propose-amendment",
        command="governance",
        subcommand="propose_amendment",
        title="Đệ trình đề xuất sửa đổi hiến pháp doanh nghiệp (Constitutional Amendment Proposal L0)",
        description=(
            "Create a tiered constitutional amendment proposal with threshold and quorum "
            "rules via GovernanceEngine, persisting it to workspace governance.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "minLength": 3, "maxLength": 200},
                "description": {"type": "string", "minLength": 5, "maxLength": 500},
                "amendment_text": {"type": "string", "minLength": 10, "maxLength": 2000},
                "proposer": {"type": "string", "default": "founder"},
                "tier": {"type": "string", "enum": ["soft", "moderate", "hard"], "default": "soft"},
            },
            "required": ["title", "description", "amendment_text"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_csuite_bizops_wave5:governance_propose_amendment",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/governance.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": ["proposal_id", "title", "tier", "status"],
                },
            ),
            Postcondition("echoes_input", {"param_path": "title", "result_path": "title"}),
            Postcondition(
                "enum_member",
                {"path": "tier", "allowed": ["soft", "moderate", "hard"]},
            ),
            Postcondition(
                "record_persisted",
                {"table": "proposals", "id_path": "proposal_id", "id_column": "id"},
            ),
        ),
        sop_steps=("draft-amendment-text", "assign-tier-thresholds", "persist-proposal"),
        department_id="ceo-command",
        layer_id="L0",
        gate_id="company-blueprint",
        jurisdiction="GLOBAL",
        rule_version="Mekong Constitutional Proposal Registry v1",
        output_contract={"evidence_type": "GOVERNANCE_PROPOSAL_RECORD"},
        test_id=f"{TEST_MODULE}::test_governance_propose_amendment_and_ballot_tally",
    ),
    OperationSpec(
        op_id="governance.tally-ballot",
        command="governance",
        subcommand="tally_ballot",
        title="Bỏ phiếu có trọng số & công bố kết quả biểu quyết (Weighted Ballot Tally L0)",
        description=(
            "Cast a weighted constitutional vote and tally the ballot with quorum and "
            "approval-rate verification via GovernanceEngine in workspace governance.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "minLength": 3, "maxLength": 200},
                "amendment_text": {"type": "string", "minLength": 10, "maxLength": 2000},
                "voter": {"type": "string", "default": "founder"},
                "choice": {"type": "string", "enum": ["yes", "no", "abstain"], "default": "yes"},
                "weight": {"type": "number", "exclusiveMinimum": 0, "maximum": 1000, "default": 3.0},
                "tier": {"type": "string", "enum": ["soft", "moderate", "hard"], "default": "soft"},
            },
            "required": ["title", "amendment_text"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_csuite_bizops_wave5:governance_tally_ballot",
        ),
        effects=(
            "WRITE:.mekong/workspaces/{workspace_id}/governance.db",
        ),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": ["proposal_id", "title", "status", "approval_rate", "quorum_met"],
                },
            ),
            Postcondition("echoes_input", {"param_path": "title", "result_path": "title"}),
            Postcondition("value_bounds", {"path": "approval_rate", "min": 0, "max": 100}),
            Postcondition("enum_member", {"path": "status", "allowed": ["passed", "rejected", "voting"]}),
            Postcondition(
                "record_persisted",
                {"table": "votes", "id_path": "proposal_id", "id_column": "proposal_id"},
            ),
        ),
        sop_steps=("open-ballot", "cast-weighted-vote", "tally-quorum-outcome"),
        department_id="ceo-command",
        layer_id="L0",
        gate_id="company-blueprint",
        jurisdiction="GLOBAL",
        rule_version="Mekong Weighted Ballot Tally v1",
        output_contract={"evidence_type": "GOVERNANCE_BALLOT_RECORD"},
        test_id=f"{TEST_MODULE}::test_governance_propose_amendment_and_ballot_tally",
    ),
    OperationSpec(
        op_id="binh-phap.assess-terrain",
        command="binh-phap",
        subcommand="assess_terrain",
        title="Đánh giá thế đất thị trường & xác suất thắng (Nine Terrains Assessment L0)",
        description=(
            "Evaluate competitive market terrain and win probability from relative strength "
            "under Sun Tzu's Art of War, persisting assessment to workspace binh_phap.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "competitor_name": {"type": "string", "minLength": 2, "maxLength": 200},
                "market_segment": {"type": "string", "minLength": 2, "maxLength": 200},
                "terrain_type": {
                    "type": "string",
                    "enum": ["ACCESSIBLE_GROUND", "ENTANGLING_GROUND", "PRECIPITOUS_GROUND", "DEATH_GROUND"],
                    "default": "ACCESSIBLE_GROUND",
                },
                "relative_strength_ratio": {
                    "type": "number",
                    "exclusiveMinimum": 0,
                    "maximum": 20,
                    "default": 1.4,
                },
            },
            "required": ["competitor_name", "market_segment"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_csuite_bizops_wave5:binh_phap_assess_terrain",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/binh_phap.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "maneuver_id",
                        "competitor_name",
                        "market_segment",
                        "win_probability_pct",
                        "strategic_chapter",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "competitor_name", "result_path": "competitor_name"}),
            Postcondition("value_bounds", {"path": "win_probability_pct", "min": 25, "max": 98}),
            Postcondition(
                "enum_member",
                {"path": "posture_status", "allowed": ["TERRAIN_ASSESSED"]},
            ),
            Postcondition(
                "record_persisted",
                {"table": "binh_phap_campaigns", "id_path": "maneuver_id", "id_column": "maneuver_id"},
            ),
        ),
        sop_steps=("map-competitive-terrain", "score-win-probability", "persist-terrain-assessment"),
        department_id="ceo-command",
        layer_id="L0",
        gate_id="company-blueprint",
        jurisdiction="GLOBAL",
        rule_version="Mekong Binh Phap Terrain Assessment v1",
        output_contract={"evidence_type": "BINH_PHAP_TERRAIN_RECORD"},
        test_id=f"{TEST_MODULE}::test_binh_phap_assess_terrain_and_founder_committed_maneuver",
    ),
    OperationSpec(
        op_id="binh-phap.commit-maneuver",
        command="binh-phap",
        subcommand="commit_maneuver",
        title="Cam kết triển khai binh pháp & cấp ngân sách tác chiến (Maneuver Commitment L0)",
        description=(
            "Commit a strategic maneuver doctrine with a battle budget, persisting the "
            "committed campaign posture to workspace binh_phap.db after founder confirmation."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "competitor_name": {"type": "string", "minLength": 2, "maxLength": 200},
                "market_segment": {"type": "string", "minLength": 2, "maxLength": 200},
                "capital_budget_vnd": {"type": "number", "minimum": 0, "maximum": 1_000_000_000_000},
                "maneuver_doctrine": {
                    "type": "string",
                    "enum": ["ORTHODOX_HOLD_UNORTHODOX_STRIKE", "FLANK_ENCIRCLEMENT", "ATTACK_BY_STRATAGEM"],
                    "default": "ORTHODOX_HOLD_UNORTHODOX_STRIKE",
                },
            },
            "required": ["competitor_name", "market_segment", "capital_budget_vnd"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_csuite_bizops_wave5:binh_phap_commit_maneuver",
        ),
        approval_policy="FOUNDER_CONFIRMATION",
        effects=(
            "WRITE:.mekong/workspaces/{workspace_id}/binh_phap.db",
            "WRITE:.mekong/promise_evidence.db",
        ),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "maneuver_id",
                        "competitor_name",
                        "maneuver_doctrine",
                        "capital_budget_vnd",
                        "posture_status",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "competitor_name", "result_path": "competitor_name"}),
            Postcondition("value_bounds", {"path": "capital_budget_vnd", "min": 0, "max": 1_000_000_000_000}),
            Postcondition(
                "enum_member",
                {"path": "posture_status", "allowed": ["MANEUVER_COMMITTED"]},
            ),
            Postcondition(
                "record_persisted",
                {"table": "binh_phap_campaigns", "id_path": "maneuver_id", "id_column": "maneuver_id"},
            ),
        ),
        sop_steps=("verify-founder-authority", "bind-doctrine-budget", "commit-maneuver"),
        department_id="ceo-command",
        layer_id="L0",
        gate_id="company-blueprint",
        jurisdiction="GLOBAL",
        rule_version="Mekong Maneuver Commitment Seal v1",
        output_contract={"evidence_type": "BINH_PHAP_COMMITMENT_SEAL"},
        test_id=f"{TEST_MODULE}::test_binh_phap_assess_terrain_and_founder_committed_maneuver",
    ),
)

QUALITY_COMPLIANCE_OPS: tuple[OperationSpec, ...] = (
    OperationSpec(
        op_id="csuite.convene-council",
        command="csuite",
        subcommand="convene_council",
        title="Triệu tập Hội đồng C-Suite AI hợp nhất (Unified Board Council L2)",
        description=(
            "Convene the unified AI C-Suite council (CFO, CMO, CSO, CTO) against an agenda "
            "and record the consensus resolution to workspace csuite.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "agenda_title": {"type": "string", "minLength": 3, "maxLength": 240},
                "directive_summary": {"type": "string", "minLength": 5, "maxLength": 600},
                "participating_officers": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["CEO", "CFO", "CMO", "CSO", "CTO"]},
                },
            },
            "required": ["agenda_title", "directive_summary"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_csuite_bizops_wave5:csuite_convene_council",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/csuite.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": ["resolution_id", "agenda_title", "consensus_score", "board_status"],
                },
            ),
            Postcondition("echoes_input", {"param_path": "agenda_title", "result_path": "agenda_title"}),
            Postcondition("value_bounds", {"path": "consensus_score", "min": 0, "max": 100}),
            Postcondition(
                "enum_member",
                {"path": "board_status", "allowed": ["COUNCIL_DELIBERATED"]},
            ),
            Postcondition(
                "record_persisted",
                {
                    "table": "csuite_resolutions",
                    "id_path": "resolution_id",
                    "id_column": "resolution_id",
                },
            ),
        ),
        sop_steps=("assemble-quorum", "deliberate-agenda", "persist-council-resolution"),
        department_id="quality-compliance",
        layer_id="L2",
        gate_id="mvp-live",
        jurisdiction="GLOBAL",
        rule_version="Mekong Unified C-Suite Council v1",
        output_contract={"evidence_type": "CSUITE_COUNCIL_RECORD"},
        test_id=f"{TEST_MODULE}::test_csuite_convene_council_and_founder_ratified_directive",
    ),
    OperationSpec(
        op_id="csuite.ratify-directive",
        command="csuite",
        subcommand="ratify_directive",
        title="Phê duyệt Nghị quyết Hội đồng Quản trị (Board Directive Ratification L2)",
        description=(
            "Ratify a cross-functional board directive with budget impact and persist the "
            "ratified resolution to workspace csuite.db after founder confirmation."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "agenda_title": {"type": "string", "minLength": 3, "maxLength": 240},
                "directive_summary": {"type": "string", "minLength": 5, "maxLength": 600},
                "budget_impact_vnd": {"type": "number", "minimum": 0, "maximum": 100_000_000_000_000},
            },
            "required": ["agenda_title", "directive_summary", "budget_impact_vnd"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_csuite_bizops_wave5:csuite_ratify_directive",
        ),
        approval_policy="FOUNDER_CONFIRMATION",
        effects=(
            "WRITE:.mekong/workspaces/{workspace_id}/csuite.db",
            "WRITE:.mekong/promise_evidence.db",
        ),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "resolution_id",
                        "agenda_title",
                        "directive_summary",
                        "budget_impact_vnd",
                        "board_status",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "directive_summary", "result_path": "directive_summary"}),
            Postcondition("value_bounds", {"path": "budget_impact_vnd", "min": 0, "max": 100_000_000_000_000}),
            Postcondition(
                "enum_member",
                {"path": "board_status", "allowed": ["DIRECTIVE_RATIFIED"]},
            ),
            Postcondition(
                "record_persisted",
                {
                    "table": "csuite_resolutions",
                    "id_path": "resolution_id",
                    "id_column": "resolution_id",
                },
            ),
        ),
        sop_steps=("verify-founder-authority", "bind-directive-budget", "ratify-board-resolution"),
        department_id="quality-compliance",
        layer_id="L2",
        gate_id="mvp-live",
        jurisdiction="GLOBAL",
        rule_version="Mekong Board Directive Ratification v1",
        output_contract={"evidence_type": "CSUITE_DIRECTIVE_SEAL"},
        test_id=f"{TEST_MODULE}::test_csuite_convene_council_and_founder_ratified_directive",
    ),
)

SALES_REVENUE_OPS: tuple[OperationSpec, ...] = (
    OperationSpec(
        op_id="zenpay.allocate-budget",
        command="zenpay",
        subcommand="allocate_budget",
        title="Phân bổ ngân sách Kho bạc Hiến pháp (Constitutional Treasury Allocation L3)",
        description=(
            "Allocate a constitutional treasury envelope to a department with a SHA-256 "
            "settlement digest, persisting the allocation to workspace zenpay.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "department_id": {"type": "string", "minLength": 2, "maxLength": 80},
                "purpose": {"type": "string", "minLength": 3, "maxLength": 300},
                "amount_vnd": {"type": "number", "exclusiveMinimum": 0, "maximum": 10_000_000_000_000},
            },
            "required": ["department_id", "purpose", "amount_vnd"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_csuite_bizops_wave5:zenpay_allocate_budget",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/zenpay.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": ["entry_id", "department_id", "amount_vnd", "treasury_status", "settlement_digest"],
                },
            ),
            Postcondition("echoes_input", {"param_path": "department_id", "result_path": "department_id"}),
            Postcondition("value_bounds", {"path": "amount_vnd", "min": 0, "max": 10_000_000_000_000}),
            Postcondition("enum_member", {"path": "treasury_status", "allowed": ["ALLOCATED"]}),
            Postcondition(
                "record_persisted",
                {
                    "table": "zenpay_treasury_ledger",
                    "id_path": "entry_id",
                    "id_column": "entry_id",
                },
            ),
        ),
        sop_steps=("authorize-envelope", "hash-settlement", "persist-allocation"),
        department_id="sales-revenue",
        layer_id="L3",
        gate_id="first-revenue",
        jurisdiction="GLOBAL",
        rule_version="Mekong Constitutional Treasury Allocation v1",
        output_contract={"evidence_type": "ZENPAY_ALLOCATION_RECORD"},
        test_id=f"{TEST_MODULE}::test_zenpay_allocate_budget_and_founder_settled_disbursement",
    ),
    OperationSpec(
        op_id="zenpay.settle-disbursement",
        command="zenpay",
        subcommand="settle_disbursement",
        title="Chi trả & quyết toán Kho bạc (Treasury Disbursement Settlement L3)",
        description=(
            "Settle an outbound treasury disbursement to a vendor account with a SHA-256 "
            "settlement digest, persisting it to workspace zenpay.db after founder confirmation."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "department_id": {"type": "string", "minLength": 2, "maxLength": 80},
                "recipient_account": {"type": "string", "minLength": 4, "maxLength": 80},
                "amount_vnd": {"type": "number", "exclusiveMinimum": 0, "maximum": 10_000_000_000_000},
                "purpose": {"type": "string", "default": "Vendor & Infrastructure Settlement"},
            },
            "required": ["department_id", "recipient_account", "amount_vnd"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_csuite_bizops_wave5:zenpay_settle_disbursement",
        ),
        approval_policy="FOUNDER_CONFIRMATION",
        effects=(
            "WRITE:.mekong/workspaces/{workspace_id}/zenpay.db",
            "WRITE:.mekong/promise_evidence.db",
        ),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "entry_id",
                        "department_id",
                        "recipient_account",
                        "amount_vnd",
                        "treasury_status",
                        "settlement_digest",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "recipient_account", "result_path": "recipient_account"}),
            Postcondition("value_bounds", {"path": "amount_vnd", "min": 0, "max": 10_000_000_000_000}),
            Postcondition("enum_member", {"path": "treasury_status", "allowed": ["DISBURSED_SETTLED"]}),
            Postcondition(
                "record_persisted",
                {
                    "table": "zenpay_treasury_ledger",
                    "id_path": "entry_id",
                    "id_column": "entry_id",
                },
            ),
        ),
        sop_steps=("verify-founder-authority", "verify-recipient-account", "settle-disbursement"),
        department_id="sales-revenue",
        layer_id="L3",
        gate_id="first-revenue",
        jurisdiction="GLOBAL",
        rule_version="Mekong Treasury Disbursement Settlement v1",
        output_contract={"evidence_type": "ZENPAY_DISBURSEMENT_SEAL"},
        test_id=f"{TEST_MODULE}::test_zenpay_allocate_budget_and_founder_settled_disbursement",
    ),
    OperationSpec(
        op_id="revenue.record-subscription",
        command="revenue",
        subcommand="record_subscription",
        title="Ghi nhận doanh thu thuê bao định kỳ (Recurring Subscription Revenue L3)",
        description=(
            "Record a recurring SaaS subscription transaction and activate the subscription "
            "via RevenueEngine in workspace revenue.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "minLength": 2, "maxLength": 120},
                "customer_name": {"type": "string", "minLength": 2, "maxLength": 200},
                "tier": {"type": "string", "enum": ["starter", "pro", "enterprise"], "default": "pro"},
                "amount_usd": {"type": "number", "exclusiveMinimum": 0, "maximum": 1_000_000, "default": 399.0},
                "gateway": {"type": "string", "enum": ["vietqr", "nowpayments", "stripe"], "default": "vietqr"},
            },
            "required": ["customer_id", "customer_name"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_csuite_bizops_wave5:revenue_record_subscription",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/revenue.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": ["transaction_id", "customer_id", "customer_name", "amount_usd", "status"],
                },
            ),
            Postcondition("echoes_input", {"param_path": "customer_id", "result_path": "customer_id"}),
            Postcondition("value_bounds", {"path": "amount_usd", "min": 0, "max": 1_000_000}),
            Postcondition("enum_member", {"path": "status", "allowed": ["succeeded"]}),
            Postcondition(
                "record_persisted",
                {"table": "transactions", "id_path": "transaction_id", "id_column": "id"},
            ),
        ),
        sop_steps=("validate-subscription-tier", "post-transaction", "activate-subscription"),
        department_id="sales-revenue",
        layer_id="L3",
        gate_id="first-revenue",
        jurisdiction="GLOBAL",
        rule_version="Mekong Subscription Revenue Ledger v1",
        output_contract={"evidence_type": "REVENUE_SUBSCRIPTION_RECORD"},
        test_id=f"{TEST_MODULE}::test_revenue_record_subscription_and_reconcile_mrr",
    ),
    OperationSpec(
        op_id="revenue.reconcile-mrr",
        command="revenue",
        subcommand="reconcile_mrr",
        title="Đối soát doanh thu MRR/ARR & dòng tiền (MRR Payment Reconciliation L3)",
        description=(
            "Reconcile active subscription MRR against collected payments via RevenueEngine "
            "and persist the reconciliation report to workspace revenue.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "minLength": 2, "maxLength": 120},
                "amount_usd": {"type": "number", "exclusiveMinimum": 0, "maximum": 1_000_000, "default": 399.0},
                "tier": {"type": "string", "enum": ["starter", "pro", "enterprise"], "default": "pro"},
                "auto_fix": {"type": "boolean", "default": True},
            },
            "required": ["customer_id"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_csuite_bizops_wave5:revenue_reconcile_mrr",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/revenue.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": ["reconciliation_id", "customer_id", "status", "total_collected"],
                },
            ),
            Postcondition("echoes_input", {"param_path": "customer_id", "result_path": "customer_id"}),
            Postcondition("value_bounds", {"path": "total_collected", "min": 0}),
            Postcondition(
                "record_persisted",
                {"table": "reconciliations", "id_path": "reconciliation_id", "id_column": "id"},
            ),
        ),
        sop_steps=("collect-active-subscriptions", "compare-expected-vs-collected", "persist-reconciliation"),
        department_id="sales-revenue",
        layer_id="L3",
        gate_id="first-revenue",
        jurisdiction="GLOBAL",
        rule_version="Mekong MRR Reconciliation Audit v1",
        output_contract={"evidence_type": "REVENUE_RECONCILIATION_RECORD"},
        test_id=f"{TEST_MODULE}::test_revenue_record_subscription_and_reconcile_mrr",
    ),
    OperationSpec(
        op_id="usage.meter-consumption",
        command="usage",
        subcommand="meter_consumption",
        title="Đo lường tiêu thụ tín dụng MCU theo tính năng (Tenant MCU Metering L3)",
        description=(
            "Record tenant MCU consumption against quota cap and compute utilization ratio "
            "in workspace usage.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "tenant_id": {"type": "string", "minLength": 2, "maxLength": 120},
                "feature_key": {"type": "string", "minLength": 2, "maxLength": 120},
                "mcu_consumed": {"type": "integer", "minimum": 0, "maximum": 10_000_000},
                "quota_cap_mcu": {"type": "integer", "minimum": 1, "maximum": 100_000_000, "default": 4000},
            },
            "required": ["tenant_id", "feature_key", "mcu_consumed"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_csuite_bizops_wave5:usage_meter_consumption",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/usage.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "meter_id",
                        "tenant_id",
                        "feature_key",
                        "mcu_consumed",
                        "utilization_pct",
                        "enforcement_action",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "tenant_id", "result_path": "tenant_id"}),
            Postcondition("value_bounds", {"path": "mcu_consumed", "min": 0, "max": 10_000_000}),
            Postcondition(
                "enum_member",
                {"path": "enforcement_action", "allowed": ["WITHIN_QUOTA", "OVERAGE_ALERT"]},
            ),
            Postcondition(
                "record_persisted",
                {"table": "usage_meters", "id_path": "meter_id", "id_column": "meter_id"},
            ),
        ),
        sop_steps=("read-feature-counter", "compute-utilization-pct", "persist-usage-meter"),
        department_id="sales-revenue",
        layer_id="L3",
        gate_id="first-revenue",
        jurisdiction="GLOBAL",
        rule_version="Mekong MCU Metering Engine v1",
        output_contract={"evidence_type": "USAGE_METER_RECORD"},
        test_id=f"{TEST_MODULE}::test_usage_meter_consumption_and_founder_enforced_quota_cap",
    ),
    OperationSpec(
        op_id="usage.enforce-quota-cap",
        command="usage",
        subcommand="enforce_quota_cap",
        title="Áp trần hạn mức MCU & khóa vượt ngưỡng (Hard MCU Quota Cap Enforcement L3)",
        description=(
            "Enforce a hard MCU quota cap policy (HTTP 402 throttle on depletion) in "
            "workspace usage.db after founder confirmation."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "tenant_id": {"type": "string", "minLength": 2, "maxLength": 120},
                "quota_cap_mcu": {"type": "integer", "minimum": 1, "maximum": 100_000_000},
                "enforcement_mode": {
                    "type": "string",
                    "enum": ["HARD_THROTTLE_402", "SOFT_WARN_ONLY"],
                    "default": "HARD_THROTTLE_402",
                },
            },
            "required": ["tenant_id", "quota_cap_mcu"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_csuite_bizops_wave5:usage_enforce_quota_cap",
        ),
        approval_policy="FOUNDER_CONFIRMATION",
        effects=(
            "WRITE:.mekong/workspaces/{workspace_id}/usage.db",
            "WRITE:.mekong/promise_evidence.db",
        ),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": ["meter_id", "tenant_id", "quota_cap_mcu", "enforcement_action"],
                },
            ),
            Postcondition("echoes_input", {"param_path": "tenant_id", "result_path": "tenant_id"}),
            Postcondition("value_bounds", {"path": "quota_cap_mcu", "min": 1, "max": 100_000_000}),
            Postcondition(
                "enum_member",
                {"path": "enforcement_action", "allowed": ["HARD_THROTTLE_402", "SOFT_WARN_ONLY"]},
            ),
            Postcondition(
                "record_persisted",
                {"table": "usage_meters", "id_path": "meter_id", "id_column": "meter_id"},
            ),
        ),
        sop_steps=("verify-founder-authority", "bind-quota-cap", "enforce-throttle-policy"),
        department_id="sales-revenue",
        layer_id="L3",
        gate_id="first-revenue",
        jurisdiction="GLOBAL",
        rule_version="Mekong Hard MCU Quota Cap Policy v1",
        output_contract={"evidence_type": "USAGE_QUOTA_CAP_SEAL"},
        test_id=f"{TEST_MODULE}::test_usage_meter_consumption_and_founder_enforced_quota_cap",
    ),
    OperationSpec(
        op_id="consulting.create-engagement",
        command="consulting",
        subcommand="create_engagement",
        title="Khởi tạo hợp đồng tư vấn giải pháp AI (Consulting Engagement Creation L3)",
        description=(
            "Create a B2B consulting engagement record with service tier and pricing via "
            "ConsultingEngine in workspace consulting.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "client_name": {"type": "string", "minLength": 2, "maxLength": 200},
                "service_tier": {
                    "type": "string",
                    "enum": ["audit", "custom_agent", "full_stack", "retainer"],
                    "default": "custom_agent",
                },
                "price_usd": {"type": "number", "exclusiveMinimum": 0, "maximum": 1_000_000, "default": 2500.0},
                "notes": {"type": "string", "default": "Digital transformation & AI agent deployment"},
            },
            "required": ["client_name"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_csuite_bizops_wave5:consulting_create_engagement",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/consulting.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": ["engagement_id", "client_name", "service_tier", "price_usd", "status"],
                },
            ),
            Postcondition("echoes_input", {"param_path": "client_name", "result_path": "client_name"}),
            Postcondition("value_bounds", {"path": "price_usd", "min": 0, "max": 1_000_000}),
            Postcondition(
                "record_persisted",
                {"table": "engagements", "id_path": "engagement_id", "id_column": "id"},
            ),
        ),
        sop_steps=("scope-engagement-tier", "calculate-engagement-fee", "persist-engagement"),
        department_id="sales-revenue",
        layer_id="L3",
        gate_id="first-revenue",
        jurisdiction="GLOBAL",
        rule_version="Mekong Consulting Engagement Registry v1",
        output_contract={"evidence_type": "CONSULTING_ENGAGEMENT_RECORD"},
        test_id=f"{TEST_MODULE}::test_consulting_create_engagement_and_generate_proposal",
    ),
    OperationSpec(
        op_id="consulting.generate-proposal",
        command="consulting",
        subcommand="generate_proposal",
        title="Lập đề xuất kỹ thuật & báo giá chuyển đổi số (Consulting Architecture Proposal L3)",
        description=(
            "Generate a consulting architecture proposal with milestones and USD/VND pricing "
            "via ConsultingEngine, persisting it to workspace consulting.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "prospect_name": {"type": "string", "minLength": 2, "maxLength": 200},
                "service_tier": {
                    "type": "string",
                    "enum": ["audit", "custom_agent", "full_stack", "retainer"],
                    "default": "custom_agent",
                },
                "requirements": {
                    "type": "string",
                    "default": "Automate Zalo OA, e-invoicing and statutory tax filing",
                },
                "industry": {"type": "string", "default": "Technology"},
            },
            "required": ["prospect_name"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_csuite_bizops_wave5:consulting_generate_proposal",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/consulting.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": ["proposal_id", "prospect_name", "service_tier", "price_usd", "price_vnd"],
                },
            ),
            Postcondition("echoes_input", {"param_path": "prospect_name", "result_path": "prospect_name"}),
            Postcondition("value_bounds", {"path": "price_usd", "min": 0}),
            Postcondition(
                "record_persisted",
                {"table": "proposals", "id_path": "proposal_id", "id_column": "id"},
            ),
        ),
        sop_steps=("analyze-client-requirements", "draft-milestone-architecture", "persist-proposal"),
        department_id="sales-revenue",
        layer_id="L3",
        gate_id="first-revenue",
        jurisdiction="GLOBAL",
        rule_version="Mekong Consulting Proposal Generator v1",
        output_contract={"evidence_type": "CONSULTING_PROPOSAL_RECORD"},
        test_id=f"{TEST_MODULE}::test_consulting_create_engagement_and_generate_proposal",
    ),
)

GROWTH_MARKETING_OPS: tuple[OperationSpec, ...] = (
    OperationSpec(
        op_id="content.produce-asset",
        command="content",
        subcommand="produce_asset",
        title="Sản xuất nội dung đa định dạng chuẩn SEO (SEO Content Asset Production L3)",
        description=(
            "Generate and persist a structured content asset across content pillars via "
            "ContentEngine in workspace content.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "pillar": {
                    "type": "string",
                    "enum": ["ai_automation", "founder_journey", "vietnam_tech", "product_updates"],
                    "default": "ai_automation",
                },
                "format_type": {
                    "type": "string",
                    "enum": ["blog", "post", "thread", "newsletter", "video_script"],
                    "default": "blog",
                },
                "topic": {"type": "string", "minLength": 3, "maxLength": 240},
                "channel": {"type": "string", "default": "linkedin"},
            },
            "required": ["topic"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_csuite_bizops_wave5:content_produce_asset",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/content.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": ["content_id", "pillar", "format", "channel", "status", "topic"],
                },
            ),
            Postcondition("echoes_input", {"param_path": "topic", "result_path": "topic"}),
            Postcondition(
                "record_persisted",
                {"table": "content_items", "id_path": "content_id", "id_column": "id"},
            ),
        ),
        sop_steps=("select-content-pillar", "synthesize-seo-body", "persist-content-item"),
        department_id="growth-marketing",
        layer_id="L3",
        gate_id="repeatable-channel",
        jurisdiction="GLOBAL",
        rule_version="Mekong Content Factory Engine v1",
        output_contract={"evidence_type": "CONTENT_ASSET_RECORD"},
        test_id=f"{TEST_MODULE}::test_content_produce_asset_and_schedule_publication",
    ),
    OperationSpec(
        op_id="content.schedule-publication",
        command="content",
        subcommand="schedule_publication",
        title="Lên lịch & xuất bản nội dung đa kênh (Omnichannel Content Publication L3)",
        description=(
            "Create and transition a content asset to scheduled or published status on a "
            "distribution channel via ContentEngine in workspace content.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "topic": {"type": "string", "minLength": 3, "maxLength": 240},
                "channel": {"type": "string", "default": "linkedin"},
                "pillar": {"type": "string", "default": "ai_automation"},
                "new_status": {
                    "type": "string",
                    "enum": ["scheduled", "published", "draft"],
                    "default": "published",
                },
            },
            "required": ["topic"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_csuite_bizops_wave5:content_schedule_publication",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/content.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": ["content_id", "topic", "channel", "status", "success"],
                },
            ),
            Postcondition("echoes_input", {"param_path": "topic", "result_path": "topic"}),
            Postcondition("enum_member", {"path": "status", "allowed": ["scheduled", "published", "draft"]}),
            Postcondition(
                "record_persisted",
                {"table": "content_items", "id_path": "content_id", "id_column": "id"},
            ),
        ),
        sop_steps=("prepare-channel-payload", "update-publication-status", "persist-channel-event"),
        department_id="growth-marketing",
        layer_id="L3",
        gate_id="repeatable-channel",
        jurisdiction="GLOBAL",
        rule_version="Mekong Content Publication Scheduler v1",
        output_contract={"evidence_type": "CONTENT_PUBLICATION_RECORD"},
        test_id=f"{TEST_MODULE}::test_content_produce_asset_and_schedule_publication",
    ),
    OperationSpec(
        op_id="copywriting.generate-campaign-copy",
        command="copywriting",
        subcommand="generate_campaign_copy",
        title="Viết lời quảng cáo chuyển đổi cao theo công thức PAS/AIDA (Conversion Copywriting L3)",
        description=(
            "Generate and persist direct-response landing page or ad copy using PAS/AIDA/BAB "
            "formulas via CopywritingEngine in workspace copywriting.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "product_name": {"type": "string", "minLength": 2, "maxLength": 160},
                "target_audience": {"type": "string", "minLength": 2, "maxLength": 200},
                "formula": {"type": "string", "enum": ["pas", "aida", "bab", "fab", "4p"], "default": "pas"},
                "copy_type": {
                    "type": "string",
                    "enum": ["landing_page", "sales_email", "ad_copy", "social_post"],
                    "default": "landing_page",
                },
                "key_benefit": {
                    "type": "string",
                    "default": "Tự động hóa thuế, hóa đơn và CSKH Zalo 24/7",
                },
            },
            "required": ["product_name", "target_audience"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_csuite_bizops_wave5:copywriting_generate_campaign_copy",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/copywriting.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": ["project_id", "product_name", "target_audience", "formula"],
                },
            ),
            Postcondition("echoes_input", {"param_path": "product_name", "result_path": "product_name"}),
            Postcondition("enum_member", {"path": "formula", "allowed": ["pas", "aida", "bab", "fab", "4p"]}),
            Postcondition(
                "record_persisted",
                {"table": "copy_projects", "id_path": "project_id", "id_column": "id"},
            ),
        ),
        sop_steps=("apply-copywriting-formula", "synthesize-headline-and-cta", "persist-copy-project"),
        department_id="growth-marketing",
        layer_id="L3",
        gate_id="repeatable-channel",
        jurisdiction="GLOBAL",
        rule_version="Mekong Direct-Response Copywriting Engine v1",
        output_contract={"evidence_type": "COPYWRITING_PROJECT_RECORD"},
        test_id=f"{TEST_MODULE}::test_copywriting_generate_and_audit_conversion_copy",
    ),
    OperationSpec(
        op_id="copywriting.audit-conversion-copy",
        command="copywriting",
        subcommand="audit_conversion_copy",
        title="Thẩm định điểm chuyển đổi kịch bản bán hàng (Conversion Copy Audit L3)",
        description=(
            "Generate, persist, and score B2B sales copy conversion readiness via "
            "CopywritingEngine in workspace copywriting.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "product_name": {"type": "string", "minLength": 2, "maxLength": 160},
                "target_audience": {"type": "string", "minLength": 2, "maxLength": 200},
                "formula": {"type": "string", "enum": ["pas", "aida", "bab", "fab", "4p"], "default": "aida"},
                "key_benefit": {"type": "string", "default": "Tăng 3x tỷ lệ chuyển đổi khách hàng B2B"},
            },
            "required": ["product_name", "target_audience"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_csuite_bizops_wave5:copywriting_audit_conversion_copy",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/copywriting.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": ["project_id", "product_name", "conversion_score", "grade"],
                },
            ),
            Postcondition("echoes_input", {"param_path": "product_name", "result_path": "product_name"}),
            Postcondition("value_bounds", {"path": "conversion_score", "min": 70, "max": 100}),
            Postcondition("enum_member", {"path": "grade", "allowed": ["A", "B"]}),
            Postcondition(
                "record_persisted",
                {"table": "copy_projects", "id_path": "project_id", "id_column": "id"},
            ),
        ),
        sop_steps=("synthesize-sales-copy", "score-conversion-strength", "persist-copy-audit"),
        department_id="growth-marketing",
        layer_id="L3",
        gate_id="repeatable-channel",
        jurisdiction="GLOBAL",
        rule_version="Mekong Conversion Copy Readiness Audit v1",
        output_contract={"evidence_type": "COPYWRITING_AUDIT_RECORD"},
        test_id=f"{TEST_MODULE}::test_copywriting_generate_and_audit_conversion_copy",
    ),
)

PLATFORM_OPERATIONS_OPS: tuple[OperationSpec, ...] = (
    OperationSpec(
        op_id="vendor.onboard-partner",
        command="vendor",
        subcommand="onboard_partner",
        title="Đăng ký & tích hợp đối tác hạ tầng bên thứ ba (Third-Party Vendor Onboarding L2)",
        description=(
            "Onboard a third-party cloud, payment, e-invoice or CA partner with trust score "
            "and SLA tracking via VendorEngine in workspace vendor.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 2, "maxLength": 160},
                "vendor_type": {
                    "type": "string",
                    "enum": ["agent", "tool", "model", "infra", "data"],
                    "default": "infra",
                },
                "version": {"type": "string", "default": "1.0.0"},
                "description": {"type": "string", "default": "Third-party cloud & e-invoice provider"},
                "trust_score": {"type": "number", "minimum": 0, "maximum": 100, "default": 88.0},
            },
            "required": ["name"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_csuite_bizops_wave5:vendor_onboard_partner",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/vendor.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": ["vendor_id", "name", "vendor_type", "status", "trust_score"],
                },
            ),
            Postcondition("echoes_input", {"param_path": "name", "result_path": "name"}),
            Postcondition("value_bounds", {"path": "trust_score", "min": 0, "max": 100}),
            Postcondition(
                "record_persisted",
                {"table": "vendors", "id_path": "vendor_id", "id_column": "id"},
            ),
        ),
        sop_steps=("verify-partner-metadata", "score-initial-trust", "persist-vendor-record"),
        department_id="platform-operations",
        layer_id="L2",
        gate_id="mvp-live",
        jurisdiction="GLOBAL",
        rule_version="Mekong Vendor Partner Registry v1",
        output_contract={"evidence_type": "VENDOR_ONBOARD_RECORD"},
        test_id=f"{TEST_MODULE}::test_vendor_onboard_and_security_audit_partner",
    ),
    OperationSpec(
        op_id="vendor.audit-partner",
        command="vendor",
        subcommand="audit_partner",
        title="Kiểm toán bảo mật & SLA đối tác tích hợp (Vendor Security & SLA Audit L2)",
        description=(
            "Execute a security, compliance or performance audit on a registered partner "
            "via VendorEngine and persist the audit record to workspace vendor.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 2, "maxLength": 160},
                "audit_type": {
                    "type": "string",
                    "enum": ["security", "performance", "compliance", "cost"],
                    "default": "security",
                },
                "vendor_type": {
                    "type": "string",
                    "enum": ["agent", "tool", "model", "infra", "data"],
                    "default": "infra",
                },
            },
            "required": ["name"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_csuite_bizops_wave5:vendor_audit_partner",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/vendor.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": ["audit_id", "vendor_id", "name", "audit_type", "audit_score", "status"],
                },
            ),
            Postcondition("echoes_input", {"param_path": "name", "result_path": "name"}),
            Postcondition("value_bounds", {"path": "audit_score", "min": 0, "max": 100}),
            Postcondition(
                "record_persisted",
                {"table": "vendor_audits", "id_path": "audit_id", "id_column": "id"},
            ),
        ),
        sop_steps=("load-vendor-profile", "evaluate-security-controls", "persist-vendor-audit"),
        department_id="platform-operations",
        layer_id="L2",
        gate_id="mvp-live",
        jurisdiction="GLOBAL",
        rule_version="Mekong Vendor Security & SLA Audit v1",
        output_contract={"evidence_type": "VENDOR_AUDIT_RECORD"},
        test_id=f"{TEST_MODULE}::test_vendor_onboard_and_security_audit_partner",
    ),
)

CSUITE_BIZOPS_WAVE5_VN_OPERATIONS: tuple[OperationSpec, ...] = (
    CEO_COMMAND_OPS
    + QUALITY_COMPLIANCE_OPS
    + SALES_REVENUE_OPS
    + GROWTH_MARKETING_OPS
    + PLATFORM_OPERATIONS_OPS
)

__all__ = [
    "CEO_COMMAND_OPS",
    "CSUITE_BIZOPS_WAVE5_VN_OPERATIONS",
    "GROWTH_MARKETING_OPS",
    "PLATFORM_OPERATIONS_OPS",
    "QUALITY_COMPLIANCE_OPS",
    "SALES_REVENUE_OPS",
]

