"""Untrusted Input Quarantine Floor for customer messages, notes, and attachments."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Final

from src.opc.models import ProposalInput

_BOUNDARY_TAG: Final[str] = "untrusted_customer_input"
_INVISIBLE_CHARS_RE: Final[re.Pattern[str]] = re.compile(
    f"[{chr(0x00AD)}{chr(0x200B)}-{chr(0x200F)}{chr(0x202A)}-{chr(0x202E)}{chr(0x2060)}-{chr(0x206F)}{chr(0xFEFF)}]"
)

_INJECTION_RULES: Final[tuple[tuple[str, re.Pattern[str], float], ...]] = (
    (
        "boundary_breakout",
        re.compile(
            r"<\s*/?\s*untrusted_customer_input\b|<\s*/?\s*(?:system|developer|assistant|tool_call|function_call)\b",
            re.IGNORECASE,
        ),
        1.0,
    ),
    (
        "en_instruction_override",
        re.compile(
            r"\b(?:ignore|disregard|forget|override|bypass)\b.{0,40}\b(?:previous|prior|above|all|system|developer|safety|security|instructions?|rules?|prompts?|constraints?|guardrails?)\b"
            r"|\bnew\s+(?:system\s+)?instructions?\s*:"
            r"|\bfrom\s+now\s+on\s*,?\s*(?:you\s+are|ignore|act\s+as|do\s+not)\b",
            re.IGNORECASE | re.DOTALL,
        ),
        0.95,
    ),
    (
        "vi_instruction_override",
        re.compile(
            r"(?:bỏ\s+qua|phớt\s+lờ|quên\s+(?:hết|tất\s+cả)?|xóa\s+bỏ|vô\s+hiệu\s+hóa|ghi\s+đè)\s+.{0,45}(?:hướng\s+dẫn|quy\s+tắc|lệnh|chỉ\s+thị|ràng\s+buộc|hệ\s+thống|trước\s+đó|ở\s+trên)"
            r"|(?:từ\s+bây\s+giờ|kể\s+từ\s+giờ)\s*(?:hãy\s+)?(?:bỏ\s+qua|làm\s+theo\s+lệnh\s+mới|đóng\s+vai|bạn\s+là\s+admin)",
            re.IGNORECASE | re.DOTALL,
        ),
        0.95,
    ),
    (
        "role_spoofing",
        re.compile(
            r"(?:\[\s*(?:system|developer|admin|root|owner)\s*\]|<\|im_start\|>|<\|system\|>|###\s*(?:system|instruction|developer)\b|(?:^|\n)\s*(?:system\s+prompt|developer\s+mode|dan\s+mode|jailbreak)\s*:)",
            re.IGNORECASE,
        ),
        0.95,
    ),
    (
        "approval_bypass",
        re.compile(
            r"\b(?:auto[-_\s]?approve|bypass[-_\s]?approval|skip[-_\s]?approval|force[-_\s]?approve|issue_token|verify_and_consume|ApprovalDecision\.APPROVE|MEKONG_APPROVAL_SECRET)\b"
            r"|(?:tự\s+động\s+(?:phê\s+)?duyệt|bỏ\s+qua\s+(?:bước\s+)?(?:phê\s+)?duyệt|duyệt\s+ngay\s+không\s+cần\s+hỏi|giả\s+mạo\s+chữ\s+ký\s+duyệt|khỏi\s+cần\s+chủ\s+shop\s+duyệt)",
            re.IGNORECASE,
        ),
        1.0,
    ),
    (
        "payment_or_price_hijack",
        re.compile(
            r"(?:đổi|thay\s+đổi|chuyển|sửa|cập\s+nhật|ghi\s+đè)\s+.{0,35}(?:số\s+tài\s+khoản|stk|tài\s+khoản\s+nhận|ngân\s+hàng\s+nhận|mã\s+vietqr|người\s+thụ\s+hưởng)"
            r"|(?:chuyển\s+khoản|thanh\s+toán|nhận\s+tiền)\s+(?:vào|sang|qua)\s+(?:stk|số\s+tài\s+khoản|tài\s+khoản\s+mới)\s*[:#]?\s*\d{6,}"
            r"|(?:sửa|đặt\s+lại|ghi\s+đè|ép)\s+(?:tổng\s+)?(?:giá|báo\s+giá|số\s+tiền|đơn\s+giá)\s*(?:về|thành|=)\s*(?:0|1\s*đ|1\s*vnd|miễn\s+phí)"
            r"|(?:giảm\s+giá\s+100\s*%\s*miễn\s+phí\s+hoàn\s+toàn)"
            r"|\b(?:override|set|change|swap|redirect)\b.{0,35}\b(?:price|total_amount|budget_amount|unit_price|recipient|bank\s+account|beneficiary|iban|vietqr)\b.{0,25}\b(?:to\s+0|to\s+free|to\s+attacker|to\s+account|\d{6,})\b"
            r"|\bwire\s+(?:all\s+)?funds?\s+to\s+account\b",
            re.IGNORECASE | re.DOTALL,
        ),
        1.0,
    ),
    (
        "tool_or_code_execution",
        re.compile(
            r"\bos\.system\b"
            r"|\bsubprocess\.(?:Popen|run|call)\b"
            r"|\b(?:eval|exec|__import__|call_tool|invoke_tool|execute_approved_action|verify_and_consume)\s*\("
            r"|\b(?:DROP\s+TABLE|DELETE\s+FROM\s+opc_|UNION\s+SELECT|INSERT\s+INTO\s+opc_approvals|UPDATE\s+opc_approvals\s+SET)\b"
            r"|\bCREATE\s+(?:OR\s+REPLACE\s+)?TRIGGER\b"
            r"|(?:rm\s+-rf\s+/|curl\s+https?://\S+\s*\|\s*(?:sh|bash))",
            re.IGNORECASE,
        ),
        1.0,
    ),
    (
        "secret_exfiltration",
        re.compile(
            r"\b(?:print|dump|leak|exfiltrate|send|reveal|show)\b.{0,35}\b(?:env|environ|secret|api[-_\s]?key|private[-_\s]?key|access[-_\s]?token|hmac|password|credentials?)\b"
            r"|(?:tiết\s+lộ|in\s+ra|gửi\s+ra\s+ngoài|đọc\s+file|xuất\s+ra)\s+.{0,35}(?:khóa\s+bí\s+mật|mật\s+khẩu|biến\s+môi\s+trường|api\s*key|token\s+admin|\.env)",
            re.IGNORECASE | re.DOTALL,
        ),
        1.0,
    ),
)


class QuarantineViolationError(PermissionError):
    """Raised when untrusted input fails quarantine inspection before tool execution."""


@dataclass(frozen=True)
class QuarantinedInput:
    """Immutable quarantine inspection record with neutralized boundary wrapping."""
    source: str
    raw_text: str
    wrapped_text: str
    is_safe: bool
    risk_score: float
    matched_rules: tuple[str, ...]
    tool_invocation_allowed: bool = False


def _sanitize_boundary(text: str) -> str:
    """Neutralize any attempt to close, forge, or open a second untrusted boundary tag."""
    return re.sub(
        r"<\s*(/?)\s*untrusted_customer_input([^<>]*?)(/?\s*)>?",
        r"[neutralized_tag:\1untrusted_customer_input]",
        text,
        flags=re.IGNORECASE,
    )


class QuarantineFloor:
    """Deterministic quarantine gate isolating untrusted customer text from tool execution."""

    def inspect(self, text: str, source: str = "zalo_message") -> QuarantinedInput:
        """Inspect untrusted text, wrap it in neutralized boundary tags, and compute safety."""
        # Normalize decomposed Vietnamese diacritics (NFD -> NFC) and strip zero-width/invisible
        # formatting characters so obfuscated keywords or boundary tags cannot evade regex rules.
        raw = _INVISIBLE_CHARS_RE.sub("", unicodedata.normalize("NFC", text or ""))
        safe_source = re.sub(r"[^a-zA-Z0-9_.:-]", "_", source or "untrusted")
        matched: list[str] = []
        max_score = 0.0

        for rule_id, pattern, weight in _INJECTION_RULES:
            if pattern.search(raw):
                matched.append(rule_id)
                if weight > max_score:
                    max_score = weight

        sanitized = _sanitize_boundary(raw)
        wrapped = f"<{_BOUNDARY_TAG} source=\"{safe_source}\">\n{sanitized}\n</{_BOUNDARY_TAG}>"
        is_safe = len(matched) == 0
        return QuarantinedInput(
            source=safe_source,
            raw_text=raw,
            wrapped_text=wrapped,
            is_safe=is_safe,
            risk_score=round(max_score, 4),
            matched_rules=tuple(matched),
            tool_invocation_allowed=False,
        )

    def guard_proposal_input(self, intake: ProposalInput) -> QuarantinedInput:
        """Inspect all untrusted fields on a ProposalInput before draft or tool execution."""
        combined = "\n".join(
            part
            for part in (
                intake.client_name,
                intake.client_contact,
                intake.project_title,
                intake.notes,
                " ".join(intake.requested_services),
                " ".join(intake.attachments),
            )
            if part
        )
        return self.inspect(combined, source=f"proposal_input:{intake.request_id}")

    def enforce_before_tool(self, quarantined: QuarantinedInput) -> None:
        """Block downstream tool or quote execution when quarantine flagged the input."""
        if not quarantined.is_safe:
            rules_str = ", ".join(quarantined.matched_rules)
            raise QuarantineViolationError(
                f"QuarantineFloor blocked untrusted input from '{quarantined.source}' "
                f"(risk={quarantined.risk_score}, matched=[{rules_str}])."
            )
