"""
Constitutional AI — Ethical review middleware for Mekong CLI.

Implements 9 core principles that evaluate actions before execution.
Provides a review() method for pre-flight checks and scoring.

Pattern: Each principle returns (passed: bool, score: float 0-1, reason: str)
Overall constitutional_score = weighted average of principle scores.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class Principle(Enum):
    """9 Constitutional Principles"""

    SAFETY = "safety"  # No harm to users, systems, or data
    FAIRNESS = "fairness"  # No discriminatory bias or unfair treatment
    PRIVACY = "privacy"  # Personal data protection and consent
    TRANSPARENCY = "transparency"  # Clear, explainable actions and decisions
    ACCOUNTABILITY = "accountability"  # Clear responsibility for outcomes
    HUMAN_OVERSIGHT = "human_oversight"  # Humans in critical decision loops
    SECURITY = "security"  # Protection against unauthorized access
    BENEFICENCE = "beneficence"  # Actions should benefit users/system
    SUSTAINABILITY = "sustainability"  # Resource-conscious, long-term viable


@dataclass
class PrincipleResult:
    """Result from a single principle evaluation."""

    principle: Principle
    passed: bool
    score: float  # 0.0 to 1.0
    reason: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class ConstitutionalReview:
    """Complete constitutional review result."""

    overall_score: float  # 0.0 to 1.0
    passed: bool  # True if all principles meet minimum threshold
    principle_results: List[PrincipleResult]
    blocked: bool  # True if action should be blocked
    summary: str

    # Thresholds
    MIN_SCORE_PER_PRINCIPLE: float = 0.6
    MIN_OVERALL_SCORE: float = 0.7

    def is_compliant(self) -> bool:
        """Check if review meets compliance thresholds."""
        if self.blocked:
            return False
        if self.overall_score < self.MIN_OVERALL_SCORE:
            return False
        for result in self.principle_results:
            if result.score < self.MIN_SCORE_PER_PRINCIPLE:
                return False
        return True


class Constitution:
    """
    Core Constitutional AI engine.

    Evaluates actions against 9 principles using rule-based checks
    and LLM-assisted reasoning when needed.
    """

    # Principle weights for overall score calculation
    PRINCIPLE_WEIGHTS: Dict[Principle, float] = {
        Principle.SAFETY: 1.2,  # Safety is paramount
        Principle.SECURITY: 1.1,  # Security critical
        Principle.PRIVACY: 1.0,
        Principle.FAIRNESS: 1.0,
        Principle.HUMAN_OVERSIGHT: 1.0,
        Principle.ACCOUNTABILITY: 0.9,
        Principle.TRANSPARENCY: 0.9,
        Principle.BENEFICENCE: 0.8,
        Principle.SUSTAINABILITY: 0.7,
    }

    def __init__(self, llm_client: Optional[Any] = None) -> None:
        """
        Initialize Constitution engine.

        Args:
            llm_client: Optional LLM client for assisted reasoning
        """
        self.llm_client = llm_client
        self.logger = logging.getLogger(__name__)

    def review(
        self,
        action: str,
        context: Optional[Dict[str, Any]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConstitutionalReview:
        """
        Perform constitutional review of an action.

        Args:
            action: The action being reviewed (e.g., "execute_shell", "api_call")
            context: Execution context (user_id, session, environment)
            parameters: Action-specific parameters
            metadata: Additional metadata (agent, source, priority)

        Returns:
            ConstitutionalReview with scores and pass/fail status
        """
        context = context or {}
        parameters = parameters or {}
        metadata = metadata or {}

        self.logger.info(f"Constitutional review: {action}")

        # Evaluate all principles
        results: List[PrincipleResult] = []
        for principle in Principle:
            result = self._evaluate_principle(principle, action, context, parameters, metadata)
            results.append(result)

        # Calculate weighted overall score
        total_weight = sum(self.PRINCIPLE_WEIGHTS.values())
        weighted_sum = sum(
            result.score * self.PRINCIPLE_WEIGHTS[result.principle] for result in results
        )
        overall_score = weighted_sum / total_weight if total_weight > 0 else 0.0

        # Determine if any principle blocks execution
        blocked = any(
            result.score < 0.3 for result in results
        )  # Critical failure threshold

        # Generate summary
        passed_principles = [r for r in results if r.score >= ConstitutionalReview.MIN_SCORE_PER_PRINCIPLE]
        summary = (
            f"Constitutional review: {len(passed_principles)}/{len(results)} "
            f"principles passed, overall score {overall_score:.2f}"
        )

        review = ConstitutionalReview(
            overall_score=overall_score,
            passed=overall_score >= ConstitutionalReview.MIN_OVERALL_SCORE and not blocked,
            principle_results=results,
            blocked=blocked,
            summary=summary,
        )

        self.logger.info(f"Review complete: {summary}, blocked={blocked}")
        return review

    def emit_markdown(self, path: str | Path) -> Path:
        """Write a markdown summary of all principles to *path*.

        Creates parent directories automatically. Returns the resolved path.
        """
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)

        principle_descriptions: dict[Principle, str] = {
            Principle.SAFETY: "No harm to users, systems, or data.",
            Principle.FAIRNESS: "No discriminatory bias or unfair treatment.",
            Principle.PRIVACY: "Personal data protection and consent.",
            Principle.TRANSPARENCY: "Clear, explainable actions and decisions.",
            Principle.ACCOUNTABILITY: "Clear responsibility for outcomes.",
            Principle.HUMAN_OVERSIGHT: "Humans in critical decision loops.",
            Principle.SECURITY: "Protection against unauthorized access.",
            Principle.BENEFICENCE: "Actions should benefit users/system.",
            Principle.SUSTAINABILITY: "Resource-conscious, long-term viable.",
        }

        lines: list[str] = [
            "# Constitution",
            "",
            f"Generated: {datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')}",
            "",
            "## Principles",
            "",
        ]

        for principle in Principle:
            weight = self.PRINCIPLE_WEIGHTS.get(principle, 1.0)
            desc = principle_descriptions.get(principle, principle.value)
            lines.append(f"### {principle.value}")
            lines.append("")
            lines.append(desc)
            lines.append("")
            lines.append(f"**Weight:** {weight}")
            lines.append("")

        target.write_text("\n".join(lines), encoding="utf-8")
        return target.resolve()

    def _evaluate_principle(
        self,
        principle: Principle,
        action: str,
        context: Dict[str, Any],
        parameters: Dict[str, Any],
        metadata: Dict[str, Any],
    ) -> PrincipleResult:
        """
        Evaluate a single principle.

        Args:
            principle: The principle to evaluate
            action: The action being reviewed
            context: Execution context
            parameters: Action parameters
            metadata: Additional metadata

        Returns:
            PrincipleResult with score and reasoning
        """
        evaluator_map = {
            Principle.SAFETY: self._evaluate_safety,
            Principle.FAIRNESS: self._evaluate_fairness,
            Principle.PRIVACY: self._evaluate_privacy,
            Principle.TRANSPARENCY: self._evaluate_transparency,
            Principle.ACCOUNTABILITY: self._evaluate_accountability,
            Principle.HUMAN_OVERSIGHT: self._evaluate_human_oversight,
            Principle.SECURITY: self._evaluate_security,
            Principle.BENEFICENCE: self._evaluate_beneficence,
            Principle.SUSTAINABILITY: self._evaluate_sustainability,
        }

        evaluator = evaluator_map.get(principle)
        if not evaluator:
            return PrincipleResult(
                principle=principle,
                passed=True,
                score=1.0,
                reason="No evaluator implemented",
            )

        try:
            passed, score, reason, details = evaluator(action, context, parameters, metadata)
            return PrincipleResult(
                principle=principle,
                passed=passed,
                score=max(0.0, min(1.0, score)),  # Clamp to 0-1
                reason=reason,
                details=details,
            )
        except Exception as e:
            self.logger.error(f"Error evaluating {principle}: {e}")
            return PrincipleResult(
                principle=principle,
                passed=False,
                score=0.0,
                reason=f"Evaluation error: {e}",
            )

    # ------------------------------------------------------------------
    # Principle Evaluators
    # ------------------------------------------------------------------

    def _evaluate_safety(
        self, action: str, context: Dict[str, Any], parameters: Dict[str, Any], metadata: Dict[str, Any]
    ) -> Tuple[bool, float, str, Optional[Dict[str, Any]]]:
        """Safety: No harm to users, systems, or data."""
        dangerous_patterns = [
            "rm -rf /", "rm -rf /*", ":(){ :|:& };",  # Fork bomb
            "dd if=/dev/zero", "mkfs", "format",  # Disk destruction
            "> /dev/sda", "> /dev/nvme",  # Raw disk writes
            "shutdown", "reboot", "poweroff",  # System shutdown
            "kill -9 -1", "killall",  # Process killing
            "chmod -R 777", "chown -R",  # Recursive permission changes
            "sudo", "doas",  # Privilege escalation attempts
            "dd if=/dev/random", "openssl encrypt",  # Encryption without key backup
        ]

        command = parameters.get("command", "")
        no_command = not command
        command_lower = command.lower() if command else ""

        # Check dangerous patterns in command if present
        if command:
            matched_patterns = []
            for pattern in dangerous_patterns:
                if pattern in command_lower:
                    matched_patterns.append(pattern)

            if matched_patterns:
                if len(matched_patterns) == 1:
                    details = {"pattern": matched_patterns[0]}
                else:
                    details = {"patterns": matched_patterns}
                reason = f"Dangerous pattern(s) detected: {', '.join(matched_patterns)}"
                return False, 0.0, reason, details

            # Check for destructive file operations without confirmation
            destructive_ops = ["rm ", "del ", "unlink ", "truncate "]
            if any(op in command_lower for op in destructive_ops):
                # Check for --force or -f flags
                if not ("--force" in command_lower or "-f" in command_lower.split()):
                    return True, 0.7, "Destructive operation without force flag (prompted)", {"operation": "delete"}

        # Action-based safety checks
        action_lower = action.lower()

        # 1. Data deletion safety
        if "delete" in action_lower:
            if parameters.get("dry_run"):
                return True, 0.9, "Deletion in dry-run mode", None
            where_clause = parameters.get("where", "").strip()
            # Normalize whitespace
            normalized = " ".join(where_clause.split())
            if normalized in ("1=1", "1 = 1", "TRUE", "true"):
                return False, 0.0, "Unconditional data deletion", {"risk": "mass_deletion", "condition": where_clause}
            if where_clause:
                return True, 0.7, "Deletion with filter", {"filter": where_clause}
            # No where clause at all
            return False, 0.0, "Data deletion without filter", {"risk": "no_filter"}

        # 2. Dangerous file writes
        if "file_write" in action_lower or "write" in action_lower:
            path = parameters.get("path", "")
            if path == "/etc/passwd":
                return False, 0.0, "Modification of critical system file", {"path": path, "risk": "system_compromise"}
            if path.startswith("/etc/"):
                return True, 0.5, "Modification of system configuration", {"path": path}
            if path.startswith("/boot") or path.startswith("/usr/bin") or path.startswith("/bin"):
                return False, 0.0, "Modification of system binary or boot directory", {"path": path}

        # 3. Dangerous database operations
        if "db" in action_lower or "query" in action_lower:
            query = parameters.get("query", "")
            if query:
                query_lower = query.lower()
                dangerous_sql = ["drop table", "truncate", "alter table", "delete from", "update "]
                for sql_pattern in dangerous_sql:
                    if sql_pattern in query_lower:
                        # Deleting/updating without where clause is especially dangerous
                        if "delete from" in query_lower and "where" not in query_lower:
                            return False, 0.0, "Dangerous DELETE without WHERE clause", {"operation": "delete", "risk": "mass_deletion"}
                        return False, 0.1, f"Dangerous SQL operation: {sql_pattern}", {"operation": sql_pattern, "risk": "schema_change"}

        # Default: no obvious safety concerns
        if no_command:
            return True, 1.0, "No command to evaluate", None
        return True, 0.9, "No obvious safety concerns", None

    def _evaluate_fairness(
        self, action: str, context: Dict[str, Any], parameters: Dict[str, Any], metadata: Dict[str, Any]
    ) -> Tuple[bool, float, str, Optional[Dict[str, Any]]]:
        """Fairness: No discriminatory bias or unfair treatment."""
        # Check for hardcoded discriminatory filters
        sensitive_attrs = ["race", "gender", "religion", "nationality", "age", "disability"]
        command = parameters.get("command", "")

        for attr in sensitive_attrs:
            if attr in command.lower():
                # Check for filtering/sorting by sensitive attributes
                if any(op in command for op in ["filter", "select", "where", "grep "]):
                    return (
                        False,
                        0.2,
                        f"Potential discrimination via {attr} filter",
                        {"attribute": attr},
                    )

        # Check for unequal treatment in batch operations
        batch_size = parameters.get("batch_size", 0)
        if batch_size > 1000 and not parameters.get("rate_limit"):
            return (
                True,
                0.6,
                "Large batch operation without rate limiting",
                {"batch_size": batch_size},
            )

        return True, 0.9, "No fairness concerns detected", None

    def _evaluate_privacy(
        self, action: str, context: Dict[str, Any], parameters: Dict[str, Any], metadata: Dict[str, Any]
    ) -> Tuple[bool, float, str, Optional[Dict[str, Any]]]:
        """Privacy: Personal data protection and consent."""
        pii_keywords = [
            "ssn", "social security", "passport", "driver license",
            "email", "phone", "address", "birth", "medical",
            "password", "token", "secret", "api_key", "credential",
        ]

        command = parameters.get("command", "")
        output = parameters.get("output", "")

        # Check for PII in command or output
        for keyword in pii_keywords:
            if keyword in command.lower() or keyword in output.lower():
                # Check if encryption/secure handling is present
                if "encrypt" not in command.lower() and "secure" not in command.lower():
                    return (
                        False,
                        0.3,
                        f"PII handling without encryption: {keyword}",
                        {"pii_type": keyword},
                    )

        # Check for logging of sensitive data
        if "log" in action.lower() and any(k in str(parameters) for k in ["password", "token", "key"]):
            return False, 0.2, "Sensitive data may be logged", {"risk": "credential_logging"}

        return True, 0.9, "No privacy violations detected", None

    def _evaluate_transparency(
        self, action: str, context: Dict[str, Any], parameters: Dict[str, Any], metadata: Dict[str, Any]
    ) -> Tuple[bool, float, str, Optional[Dict[str, Any]]]:
        """Transparency: Clear, explainable actions and decisions."""
        # Check for black-box operations
        if action.startswith("_") and not action.startswith("__"):
            return (
                True,
                0.6,
                "Internal/private operation (may lack transparency)",
                {"operation": action},
            )

        # Check for required explainability metadata
        if metadata.get("agent") and not metadata.get("description"):
            return (
                True,
                0.7,
                "Agent action without description",
                {"agent": metadata["agent"]},
            )

        # Auto-generated content should have attribution
        if "generate" in action.lower() and not metadata.get("source"):
            return (
                True,
                0.6,
                "Generated content without source attribution",
                {"action": action},
            )

        return True, 0.85, "Action is transparent", None

    def _evaluate_accountability(
        self, action: str, context: Dict[str, Any], parameters: Dict[str, Any], metadata: Dict[str, Any]
    ) -> Tuple[bool, float, str, Optional[Dict[str, Any]]]:
        """Accountability: Clear responsibility for outcomes."""
        # Check for proper user/session tracking
        user_id = context.get("user_id") or metadata.get("user_id")
        if not user_id:
            return True, 0.5, "No user context for accountability", {"missing": "user_id"}

        # Base score with user accountability
        score = 0.9
        reason = "Accountability mechanisms present"
        details = None

        # Check for audit trail (recommendation but doesn't reduce score)
        if not metadata.get("audit_id"):
            reason = "Action without explicit audit identifier"
            details = {"recommendation": "Add audit_id"}
            # Score remains 0.9 (user_id provides strong accountability)

        # Check for irreversible operations
        irreversible = ["delete", "remove", "purge", "drop", "truncate"]
        if any(op in action.lower() for op in irreversible):
            if not parameters.get("dry_run"):
                score = 0.6
                reason = "Irreversible operation without dry-run option"
                details = {"action": action}
            # If dry_run is set, keep higher score

        return True, score, reason, details

    def _evaluate_human_oversight(
        self, action: str, context: Dict[str, Any], parameters: Dict[str, Any], metadata: Dict[str, Any]
    ) -> Tuple[bool, float, str, Optional[Dict[str, Any]]]:
        """Human Oversight: Humans in critical decision loops."""
        # High-risk actions requiring human approval
        high_risk_actions = [
            "financial_transaction", "payout", "delete_user", "deactivate",
            "legal", "compliance_violation", "data_breach", "shutdown",
        ]

        if any(risk in action.lower() for risk in high_risk_actions):
            if not context.get("human_approved"):
                return (
                    False,
                    0.2,
                    "High-risk action without human approval",
                    {"risk_category": "critical_decision"},
                )

        # Check for automated escalation
        if metadata.get("auto_generated") and not metadata.get("review_required"):
            return (
                True,
                0.5,
                "Automation without review requirement",
                {"automation_level": "high"},
            )

        return True, 0.9, "Human oversight adequate", None

    def _evaluate_security(
        self, action: str, context: Dict[str, Any], parameters: Dict[str, Any], metadata: Dict[str, Any]
    ) -> Tuple[bool, float, str, Optional[Dict[str, Any]]]:
        """Security: Protection against unauthorized access."""
        # Build a searchable string from all string parameters
        search_text = " ".join(str(v) for v in parameters.values() if isinstance(v, str))

        # Check for plaintext credentials in any parameter
        credential_patterns = [
            (r"password\s*=", "plaintext password"),
            (r"api[_-]?key\s*=", "plaintext API key"),
            (r"token\s*=", "plaintext token"),
            (r"secret\s*=", "plaintext secret"),
        ]

        import re
        for pattern, desc in credential_patterns:
            if re.search(pattern, search_text, re.IGNORECASE):
                return False, 0.1, f"Credential exposed: {desc}", {"exposure": desc}

        # Check for high-value payments without approval (fraud risk)
        if action.lower() == "payment":
            amount = parameters.get("amount", 0)
            approved = parameters.get("approved", False) or context.get("payment_approved", False)
            if amount > 100000 and not approved:
                return False, 0.1, "High-value payment without approval", {"amount": amount, "risk": "fraud"}

        # Check for insecure protocols in command (if present)
        command = parameters.get("command", "")
        if command and "http://" in command and not metadata.get("insecure_allowed"):
            return (
                True,
                0.5,
                "Insecure protocol (HTTP) detected",
                {"protocol": "http"},
            )

        # Check for proper authentication (curl/wget with insecure flags)
        if command and ("curl" in command or "wget" in command):
            if "--insecure" in command or "-k" in command.split():
                return False, 0.3, "TLS certificate validation disabled", {"risk": "mitm"}

        return True, 0.85, "No security violations", None

    def _evaluate_beneficence(
        self, action: str, context: Dict[str, Any], parameters: Dict[str, Any], metadata: Dict[str, Any]
    ) -> Tuple[bool, float, str, Optional[Dict[str, Any]]]:
        """Beneficence: Actions should benefit users/system."""
        action_lower = action.lower()

        # 1. High-level benefit_level override
        benefit_level = parameters.get("benefit_level", "").lower()
        if benefit_level in ("high", "critical", "essential"):
            return True, 0.9, "High-benefit action", None
        if benefit_level in ("low", "minimal", "trivial"):
            return True, 0.3, "Low-benefit action", {"benefit_level": benefit_level}

        # 2. Resource-intensive operations with low benefit
        resource_cost = parameters.get("resource_cost", 0)
        benefit_score = parameters.get("benefit_score", 1.0)
        if resource_cost > 100 and benefit_score < 0.3:
            return True, 0.4, "High resource cost for low-benefit action", {"cost": resource_cost, "benefit": benefit_score}

        # 3. Determine constructive/destructive nature
        constructive_ops = ["create", "build", "generate", "add", "provision", "register", "submit", "approve", "publish"]
        destructive_ops = ["delete", "remove", "purge", "drop", "truncate", "cancel", "revoke", "terminate"]

        has_constructive = any(op in action_lower for op in constructive_ops)
        has_destructive = any(op in action_lower for op in destructive_ops)

        if has_constructive and not has_destructive:
            # Purely constructive -> high score
            reason = "Constructive action with clear benefit"
            if not metadata.get("intent"):
                reason = "Constructive action (beneficial) but no explicit intent"
            return True, 0.85, reason, None
        elif has_destructive and not has_constructive:
            # Purely destructive -> warning score
            return True, 0.6, "Purely destructive action (no constructive purpose)", {"action_type": "destructive"}
        elif has_destructive and has_constructive:
            # Mixed destructive/constructive -> medium
            return True, 0.6, "Mixed destructive/constructive action", None

        # 4. No clear constructive/destructive signal
        if metadata.get("intent"):
            return True, 0.7, "Action with stated intent but unclear benefit profile", {"intent": metadata["intent"]}
        else:
            return True, 0.7, "Action with unclear benefit profile (no explicit intent)", {"intent_required": True}

    def _evaluate_sustainability(
        self, action: str, context: Dict[str, Any], parameters: Dict[str, Any], metadata: Dict[str, Any]
    ) -> Tuple[bool, float, str, Optional[Dict[str, Any]]]:
        """Sustainability: Resource-conscious, long-term viable."""
        # Check for resource limits
        max_memory = parameters.get("max_memory_mb", 0)
        if max_memory > 4096:  # > 4GB
            return (
                True,
                0.4,
                "High memory usage operation",
                {"memory_mb": max_memory},
            )

        # Check for infinite loops
        loop_keywords = ["while true", "for(;;)", "until false", "infinite"]
        command = parameters.get("command", "").lower()
        if any(keyword in command for keyword in loop_keywords):
            return False, 0.1, "Potential infinite loop detected", {"pattern": "infinite_loop"}

        # Check for efficient algorithms (if specified)
        if parameters.get("algorithm") in ["bubble_sort", "factorial_recursive"]:
            return (
                True,
                0.5,
                "Inefficient algorithm selected",
                {"algorithm": parameters["algorithm"]},
            )

        # Check for cleanup operations
        if "cleanup" in action.lower() or "gc" in action.lower():
            return True, 0.95, "Resource cleanup operation", {"operation": "cleanup"}

        return True, 0.85, "Resource usage appears sustainable", None

    # ------------------------------------------------------------------
    # LLM-Assisted Evaluation (when available)
    # ------------------------------------------------------------------

    def _llm_assisted_review(
        self, principle: Principle, action: str, context: Dict[str, Any], parameters: Dict[str, Any]
    ) -> Optional[Tuple[bool, float, str, Dict[str, Any]]]:
        """
        Use LLM for nuanced principle evaluation.

        Args:
            principle: Principle being evaluated
            action: Action being reviewed
            context: Execution context
            parameters: Action parameters

        Returns:
            (passed, score, reason, details) or None if LLM unavailable
        """
        if not self.llm_client or not hasattr(self.llm_client, "generate"):
            return None

        try:
            prompt = self._build_llm_prompt(principle, action, context, parameters)
            response = self.llm_client.generate(prompt)

            # Parse response (expect JSON-like format)
            import json
            try:
                result = json.loads(response)
                return (
                    result.get("passed", True),
                    result.get("score", 0.5),
                    result.get("reason", "LLM assessment"),
                    result.get("details", {}),
                )
            except json.JSONDecodeError:
                # Fallback: extract score from response
                return self._parse_llm_text_response(response)
        except Exception as e:
            self.logger.warning(f"LLM review failed for {principle}: {e}")
            return None

    def _build_llm_prompt(
        self, principle: Principle, action: str, context: Dict[str, Any], parameters: Dict[str, Any]
    ) -> str:
        """Build prompt for LLM-assisted principle evaluation."""
        principle_descriptions = {
            Principle.SAFETY: "No harm to users, systems, or data",
            Principle.FAIRNESS: "No discriminatory bias or unfair treatment",
            Principle.PRIVACY: "Personal data protection and consent",
            Principle.TRANSPARENCY: "Clear, explainable actions and decisions",
            Principle.ACCOUNTABILITY: "Clear responsibility for outcomes",
            Principle.HUMAN_OVERSIGHT: "Humans in critical decision loops",
            Principle.SECURITY: "Protection against unauthorized access",
            Principle.BENEFICENCE: "Actions should benefit users/system",
            Principle.SUSTAINABILITY: "Resource-conscious, long-term viable",
        }

        return f"""Evaluate this action against the "{principle.value}" principle.

Principle: {principle_descriptions[principle]}

Action: {action}
Context: {context}
Parameters: {parameters}

Respond with JSON:
{{
    "passed": true/false,
    "score": 0.0-1.0,
    "reason": "brief explanation",
    "details": {{}}
}}
"""

    def _parse_llm_text_response(self, response: str) -> Tuple[bool, float, str, Dict[str, Any]]:
        """Parse LLM text response when JSON parsing fails."""
        response_lower = response.lower()

        # Simple heuristic parsing
        if "fail" in response_lower or "violate" in response_lower:
            passed = False
        elif "pass" in response_lower or "comply" in response_lower:
            passed = True
        else:
            passed = True  # Default to pass if unclear

        # Extract score
        import re
        score_match = re.search(r"score[:\s]*([0-9.]+)", response_lower)
        score = float(score_match.group(1)) if score_match else 0.5

        return passed, score, response[:100], {}


# Global constitution instance (singleton pattern)
_default_constitution: Optional["Constitution"] = None


def get_constitution(llm_client: Optional[Any] = None) -> Constitution:
    """
    Get or create the global Constitution instance.

    Args:
        llm_client: Optional LLM client

    Returns:
        Global Constitution instance
    """
    global _default_constitution
    if _default_constitution is None:
        _default_constitution = Constitution(llm_client=llm_client)
    return _default_constitution


def reset_constitution() -> None:
    """Reset global constitution (for testing)."""
    global _default_constitution
    _default_constitution = None
