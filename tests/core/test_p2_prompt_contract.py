"""Tests for src/core/p2_prompt_contract.py."""

from __future__ import annotations


from src.core.p2_prompt_contract import (
    KNOWN_TOOLS,
    P2PromptContract,
    ValidationResult,
    render_prompt,
    validate,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _valid_contract(**overrides) -> P2PromptContract:
    """Return a fully valid contract, optionally overriding fields."""
    defaults = dict(
        objective="Scan auth module for security issues",
        output_format="markdown",
        tool_scope=["Read", "Grep"],
        escalation_rules=["BLOCKED after 3 retries"],
        context_files=[],
        max_iterations=20,
        confidence_threshold=0.85,
    )
    defaults.update(overrides)
    return P2PromptContract(**defaults)


# ---------------------------------------------------------------------------
# validate() — happy path
# ---------------------------------------------------------------------------

class TestValidateHappyPath:
    def test_valid_contract_passes(self):
        result = validate(_valid_contract())
        assert result.valid is True
        assert result.errors == []

    def test_valid_contract_no_warnings_without_missing_files(self):
        result = validate(_valid_contract())
        assert result.warnings == []

    def test_returns_validation_result_type(self):
        result = validate(_valid_contract())
        assert isinstance(result, ValidationResult)

    def test_all_known_tools_accepted(self):
        result = validate(_valid_contract(tool_scope=KNOWN_TOOLS))
        assert result.valid is True

    def test_empty_tool_scope_accepted(self):
        result = validate(_valid_contract(tool_scope=[]))
        assert result.valid is True

    def test_min_max_iterations_boundary(self):
        assert validate(_valid_contract(max_iterations=1)).valid is True
        assert validate(_valid_contract(max_iterations=50)).valid is True


# ---------------------------------------------------------------------------
# validate() — error cases
# ---------------------------------------------------------------------------

class TestValidateErrors:
    def test_empty_objective_fails(self):
        result = validate(_valid_contract(objective=""))
        assert result.valid is False
        assert any("objective" in e for e in result.errors)

    def test_whitespace_only_objective_fails(self):
        result = validate(_valid_contract(objective="   "))
        assert result.valid is False

    def test_empty_output_format_fails(self):
        result = validate(_valid_contract(output_format=""))
        assert result.valid is False
        assert any("output_format" in e for e in result.errors)

    def test_unknown_tool_generates_error(self):
        result = validate(_valid_contract(tool_scope=["Read", "SomeFakeTool"]))
        assert result.valid is False
        assert any("SomeFakeTool" in e for e in result.errors)

    def test_multiple_unknown_tools_all_reported(self):
        result = validate(_valid_contract(tool_scope=["Alpha", "Beta"]))
        assert result.valid is False
        error_text = " ".join(result.errors)
        assert "Alpha" in error_text
        assert "Beta" in error_text

    def test_max_iterations_zero_fails(self):
        result = validate(_valid_contract(max_iterations=0))
        assert result.valid is False
        assert any("max_iterations" in e for e in result.errors)

    def test_max_iterations_51_fails(self):
        result = validate(_valid_contract(max_iterations=51))
        assert result.valid is False

    def test_confidence_threshold_zero_fails(self):
        result = validate(_valid_contract(confidence_threshold=0.0))
        assert result.valid is False

    def test_confidence_threshold_above_one_fails(self):
        result = validate(_valid_contract(confidence_threshold=1.1))
        assert result.valid is False


# ---------------------------------------------------------------------------
# validate() — warnings (non-existent context files)
# ---------------------------------------------------------------------------

class TestValidateWarnings:
    def test_nonexistent_context_file_generates_warning_not_error(self, tmp_path):
        missing = str(tmp_path / "does_not_exist.py")
        result = validate(_valid_contract(context_files=[missing]))
        # Must still be valid
        assert result.valid is True
        # Must produce a warning
        assert any(missing in w for w in result.warnings)
        # Must NOT produce an error
        assert result.errors == []

    def test_existing_context_file_no_warning(self, tmp_path):
        real_file = tmp_path / "exists.py"
        real_file.write_text("# real")
        result = validate(_valid_contract(context_files=[str(real_file)]))
        assert result.valid is True
        assert result.warnings == []


# ---------------------------------------------------------------------------
# render_prompt()
# ---------------------------------------------------------------------------

class TestRenderPrompt:
    def test_includes_objective_section(self):
        contract = _valid_contract(objective="Do something important")
        prompt = render_prompt(contract)
        assert "## Objective" in prompt
        assert "Do something important" in prompt

    def test_includes_output_format_section(self):
        prompt = render_prompt(_valid_contract(output_format="json"))
        assert "## Output Format" in prompt
        assert "json" in prompt

    def test_includes_tool_scope_section(self):
        prompt = render_prompt(_valid_contract(tool_scope=["Read", "Bash"]))
        assert "## Tool Scope" in prompt
        assert "Read" in prompt
        assert "Bash" in prompt

    def test_includes_escalation_rules_section(self):
        rules = ["BLOCKED after 3 retries", "NEEDS_CONTEXT escalate to lead"]
        prompt = render_prompt(_valid_contract(escalation_rules=rules))
        assert "## Escalation Rules" in prompt
        assert "BLOCKED after 3 retries" in prompt

    def test_includes_context_files_section(self):
        prompt = render_prompt(_valid_contract(context_files=["src/core/foo.py"]))
        assert "## Context Files" in prompt
        assert "src/core/foo.py" in prompt

    def test_includes_constraints_section(self):
        prompt = render_prompt(_valid_contract(max_iterations=15, confidence_threshold=0.9))
        assert "## Constraints" in prompt
        assert "15" in prompt
        assert "0.9" in prompt

    def test_all_six_sections_present(self):
        expected_sections = [
            "## Objective",
            "## Output Format",
            "## Tool Scope",
            "## Escalation Rules",
            "## Context Files",
            "## Constraints",
        ]
        prompt = render_prompt(_valid_contract())
        for section in expected_sections:
            assert section in prompt, f"Missing section: {section}"

    def test_returns_string(self):
        assert isinstance(render_prompt(_valid_contract()), str)
