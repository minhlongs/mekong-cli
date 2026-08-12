"""Unified routing table — single source of truth for NL mekong subcommand routing.

Consolidates entries from:
- cli/tui/router.py (originating source)
- src/cli/ask_keyword_router.py (single public route_ask() API)

Both modules import from here. To add a command, update this file only.

Entry: RouteEntry(command, (vi_keywords, ...), (en_keywords, ...))

Wildcard rules (per keyword string):
- trailing * (no preceding space) → substring / phrase-prefix check
- otherwise → exact substring contains
First match wins (table order = priority).

Phase 1 update (2026-07-13): added 6 new domain families (DevOps/CI,
Database, API/Backend, Testing, Monitoring, Security), bringing total to 45+
commands. All entries use (vi_keywords, en_keywords) tuple pairs.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass(frozen=True)
class RouteEntry:
    command: str
    vi_keywords: Tuple[str, ...]
    en_keywords: Tuple[str, ...]


# ── Single source of truth ─────────────────────────────────────────────
ROUTE_TABLE: List[RouteEntry] = [
    # ── Finance / Accounting ────────────────────────────────────────────
    RouteEntry(
        "finance-budget-plan",
        ("ngân sách*", "lập ngân sách*", "dự toán*"),
        ("budget plan*", "create budget", "make budget*", "budget forecast*"),
    ),
    RouteEntry(
        "finance-monthly-close",
        ("báo cáo tài chính*", "đóng sổ*", "đóng sổ tháng*", "kết chuyển*"),
        ("monthly close*", "financial close*", "close books*"),
    ),
    RouteEntry(
        "finops-cost",
        ("quản lý chi phí*", "giảm chi phí*", "finops*"),
        ("finops cost*", "cloud cost*", "optimize cost*", "reduce cost*"),
    ),
    RouteEntry(
        "treasury-forecast",
        ("dự báo dòng tiền*", "dự báo tài chính*", "cash flow*"),
        ("treasury forecast*", "cash flow forecast*"),
    ),
    RouteEntry(
        "accounting-daily",
        ("nhập số liệu kế toán*", "sổ sách*"),
        ("accounting daily*", "daily accounting*", "bookkeeping*"),
    ),
    # ── Marketing / Content ──────────────────────────────────────────────
    RouteEntry(
        "marketing-campaign",
        (
            "triển khai chiến dịch*",
            "lập chiến dịch*",
            "chiến dịch marketing",
        ),
        (
            "build a campaign*",
            "create a campaign*",
            "marketing campaign*",
        ),
    ),
    RouteEntry(
        "marketing-seo",
        ("tối ưu seo*", "nội dung seo*", "seo*"),
        ("search engine optimization*", "seo*"),
    ),
    RouteEntry(
        "copywriting",
        (
            "bài quảng cáo*",
            "viết copy*",
            "viết bài quảng cáo*",
            "viết landing page",
            "copywriter*",
        ),
        (
            "write copy*",
            "write ad copy*",
            "landing page copy*",
            "copywrite*",
            "ad copy*",
        ),
    ),
    RouteEntry(
        "content-blog",
        ("viết blog*", "viết bài blog*", "content blog*", "bài viết*"),
        ("write blog*", "write a blog*", "blog post*", "article*"),
    ),
    # ── Sales / CRM ──────────────────────────────────────────────────────
    RouteEntry(
        "sales-pipeline",
        (
            "quản lý pipeline*",
            "quản lý khách hàng tiềm năng*",
            "sđm*",
            "sdr*",
        ),
        ("sales pipeline*", "sales crm*", "manage pipeline*"),
    ),
    RouteEntry(
        "sdr-outreach-blast",
        (
            "gửi email outreach*",
            "outreach*",
            "chào hàng*",
            "liên hệ khách hàng mới",
        ),
        ("outreach*", "cold outreach*", "email outreach*"),
    ),
    RouteEntry(
        "sales-deal-close",
        ("đóng deal*", "ký hợp đồng*", "chốt đơn*", "đóng giao dịch*"),
        ("close deal*", "close the deal*", "negotiate*"),
    ),
    # ── DevOps / CI ──────────────────────────────────────────────────────
    RouteEntry(
        "deploy",
        (
            "triển khai*",
            "đưa lên production*",
            "push live",
            "deploy*",
        ),
        (
            "push to prod*",
            "go live*",
            "deploy*",
            "release*",
            "ship*",
        ),
    ),
    RouteEntry(
        "ci-deploy",
        ("triển khai ci*", "ci deploy*", "ci/cd deploy*", "deploy ci*"),
        (
            "ci deploy*",
            "ci build*",
            "github actions deploy*",
            "ci/cd set up*",
        ),
    ),
    RouteEntry(
        "ci-run-ci",
        ("chạy ci*", "ci run*", "chạy github actions*", "chạy pipeline*"),
        (
            "run ci*",
            "run github actions*",
            "ci check*",
            "run pipeline*",
        ),
    ),
    RouteEntry(
        "ci-debugger",
        ("debug ci*", "ci lỗi*", "ci không chạy*"),
        (
            "ci debug*",
            "ci failing*",
            "ci error*",
            "ci broken*",
        ),
    ),
# ── DevOps / CI (additional aliases + infra lifecycle) ─────────────
RouteEntry(
    "cicd-deploy",
    ("triển khai cicd*", "cicd deploy*", "cicd pipeline*", "cài đặt cicd*"),
    (
        "cicd deploy*",
        "cicd pipeline*",
        "cicd setup*",
        "cicd configure*",
    ),
),
RouteEntry(
    "infra-provision",
    (
        "cấu hình hạ tầng*",
        "triển khai hạ tầng*",
        "provision*",
        "tạo cloud run*",
        "tạo máy chủ*",
    ),
    (
        "provision infra*",
        "infra setup*",
        "cloud run setup*",
        "provision server*",
        "provision worker*",
    ),
),
    # ── Database ─────────────────────────────────────────────────────────
    RouteEntry(
        "backend-db-task",
        (
            "quản lý cơ sở dữ liệu*",
            "cập nhật schema*",
            "migrate database*",
            "cấu hình database*",
            "sửa schema*",
        ),
        (
            "database task*",
            "db migrate*",
            "db schema*",
            "database admin*",
            "database setup*",
        ),
    ),
# ── Database (specific aliases) ────────────────────────────────────
RouteEntry(
    "db-migrate",
    ("chạy migration*", "migrate db*", "db migrate*", "upgrade schema*", "cập nhật schema*"),
    (
        "run database migration*",
        "db migrate*",
        "migrate database*",
        "apply migration*",
    ),
),
RouteEntry(
    "db-seed",
    ("seed dữ liệu*", "seed database*", "chạy seed*", "điền dữ liệu*"),
    (
        "seed database*",
        "db seed*",
        "seed data*",
        "populate database*",
    ),
),
RouteEntry(
    "db-query",
    (
        "chạy câu lệnh sql*",
        "query db*",
        "truy vấn database*",
        "sql query*",
        "xem dữ liệu*",
    ),
    (
        "run database query*",
        "query database*",
        "db query*",
        "sql query*",
        "view database data*",
    ),
),
    # ── API / Backend ────────────────────────────────────────────────────
    RouteEntry(
        "backend-api-build",
        (
            "xây dựng api*",
            "tạo endpoint*",
            "api route*",
            "xây backend api*",
        ),
        (
            "build api*",
            "create endpoint*",
            "api route*",
            "rest api*",
        ),
    ),
# ── API / Backend (specific aliases) ───────────────────────────────────
RouteEntry(
    "api-design",
    ("thiết kế api*", "xây api schema*", "api design*", "thiết kế endpoint*"),
    (
        "api design*",
        "design api*",
        "api schema*",
        "api contract*",
        "openapi design*",
    ),
),
RouteEntry(
    "api-test",
    ("test api*", "kiểm tra api*", "api test*", "thử api*", "kiểm thử endpoint*"),
    (
        "test api*",
        "api test*",
        "test endpoint*",
        "integration test* api",
    ),
),
    # ── Monitoring / Observability ──────────────────────────────────────
    RouteEntry(
        "metrics",
        (
            "xem metrics*",
            "đo lường chỉ số*",
            "báo cáo metrics*",
            "xem số liệu*",
        ),
        (
            "view metrics*",
            "metrics dashboard*",
            "kpi dashboard*",
            "performance metrics*",
        ),
    ),
    RouteEntry(
        "algo-status",
        (
            "trạng thái thuật toán*",
            "kiểm tra algo*",
            "algo đang chạy*",
        ),
        (
            "algo status*",
            "check algo*",
            "running algo*",
            "algorithm status*",
        ),
    ),
    RouteEntry(
        "monitoring",
        (
            "quan trắc*",
            "giám sát hệ thống*",
            "kiểm tra uptime*",
            "sức khỏe hệ thống*",
        ),
        (
            "monitoring*",
            "system health*",
            "uptime check*",
            "observability*",
        ),
    ),
RouteEntry(
    "logs-check",
    (
        "kiểm tra log*",
        "xem log*",
        "xem logs*",
        "chạy log*",
        "log check*",
    ),
    (
        "check logs*",
        "view logs*",
        "tail logs*",
        "search logs*",
    ),
),
RouteEntry(
    "metrics-dashboard",
    (
        "bảng metrics*",
        "xem dashboard*",
        "metrics dashboard*",
        "dashboard chỉ số*",
    ),
    (
        "metrics dashboard*",
        "view metrics dashboard*",
        "open metrics dashboard*",
        "dashboard*",
    ),
),
    # ── Planning / Strategy (after broad "implement/build" cook keywords
    #    so `plan` still wins when user explicitly says "build plan") ──────
    RouteEntry(
        "plan",
        (
            "lập kế hoạch*",
            "lên kế hoạch*",
            "tạo kế hoạch*",
            "kế hoạch dự án*",
            "quy hoạch*",
            "plan*",
        ),
        ("plan*", "create plan*", "build plan*", "roadmap*"),
    ),
    # ── Engineering / Build ──────────────────────────────────────────────
    RouteEntry(
        "cook",
        (
            "code*",
            "lập trình*",
            "viết code*",
            "code giao diện",
            "xây dựng backend*",
            "xây dựng frontend*",
        ),
        (
            "code*",
            "implement*",
            "develop*",
            "program*",
            "build*",
            "write code*",
        ),
    ),
    RouteEntry(
        "fix",
        (
            "sửa lỗi*",
            "sửa bug*",
            "sửa chữa*",
            "lỗi*",
            "hỏng*",
            "không chạy*",
        ),
        (
            "fix*",
            "debug*",
            "bug*",
            "broken*",
            "error*",
            "issue*",
        ),
    ),
    RouteEntry(
        "test",
        (
            "viết test*",
            "chạy test*",
            "kiểm thử*",
            "scenario*",
            "end-to-end test*",
        ),
        (
            "test*",
            "unit test*",
            "integration test*",
            "e2e test*",
            "write test*",
        ),
    ),
# ── Testing ──────────────────────────────────────────────────────────
RouteEntry(
    "e2e-test",
    (
        "chạy e2e test*",
        "e2e*",
        "kiểm tra end-to-end*",
        "test end-to-end*",
    ),
    (
        "run e2e test*",
        "e2e test*",
        "end-to-end test*",
        "playwright test*",
    ),
),
RouteEntry(
    "load-test",
    (
        "load test*",
        "kiểm tra tải*",
        "test tải*",
        "benchmark*",
        "kiểm tra hiệu năng*",
    ),
    (
        "load test*",
        "load test api*",
        "stress test*",
        "performance test*",
        "benchmark api*",
    ),
),
    # ── Analytics / Business Intelligence ────────────────────────────────
    RouteEntry(
        "analytics-report",
        (
            "xem analytics*",
            "phân tích dữ liệu*",
            "phân tích data*",
            "phân tích tài chính*",
            "báo cáo phân tích*",
        ),
        (
            "view analytics*",
            "analyze data*",
            "analytics*",
            "data analysis*",
            "run analytics*",
        ),
    ),
    RouteEntry(
        "analyst-report",
        (
            "báo cáo phân tích chi tiết*",
            "báo cáo chuyên sâu*",
            "báo cáo nghiên cứu*",
        ),
        (
            "deep analysis*",
            "research report*",
            "detailed report*",
        ),
    ),
    # ── Research / Scouting ──────────────────────────────────────────────
    RouteEntry(
        "research",
        (
            "nghiên cứu*",
            "tìm hiểu*",
            "khảo sát*",
            "điều tra*",
            "phân tích công nghệ*",
        ),
        (
            "research*",
            "investigate*",
            "look into*",
            "deep dive*",
        ),
    ),
    RouteEntry(
        "scout",
        (
            "scout*",
            "tìm file*",
            "khám phá codebase*",
            "quét codebase*",
        ),
        (
            "scout*",
            "explore codebase*",
            "find file*",
            "search code*",
        ),
    ),
    RouteEntry(
        "analyze",
        ("phân tích*", "xem xét*", "đánh giá*"),
        (
            "analyze*",
            "review*",
            "examine*",
            "assess*",
        ),
    ),
    # ── Security / Auditing ──────────────────────────────────────────────
RouteEntry(
    "vuln-scan",
    ("quét lỗ hổng*", "quét vulnerability*", "quét bảo mật*", "kiểm tra lỗ hổng*"),
    (
        "vuln scan*",
        "vulnerability scan*",
        "scan vulnerabilities*",
        "security vulnerability*",
    ),
),
RouteEntry(
    "secret-rotate",
    ("xoay vòng secret*", "rotate secret*", "cập nhật api key*", "xoay api key*"),
    (
        "rotate secrets*",
        "rotate api key*",
        "regenerate api key*",
        "secret rotation*",
    ),
),
    RouteEntry(
        "security-scan",
        ("quét bảo mật*", "kiểm tra bảo mật*", "phân tích bảo mật*"),
        ("security scan*", "security audit*", "security review*"),
    ),
    RouteEntry(
        "audit-compliance",
        ("kiểm toán*", "audit*", "compliance*", "tuân thủ*", "soát xét*"),
        (
            "audit*",
            "compliance*",
            "SOC2*",
            "sox*",
            "internal audit*",
        ),
    ),
    # ── Planning / Strategy ──────────────────────────────────────────────
    RouteEntry(
        "brainstorm",
        ("brainstorm*", "động não*", "gợi ý ý tưởng*", "ý tưởng*"),
        ("brainstorm*", "idea*", "ideate*", "brain dump*"),
    ),
    # ── Documentation ────────────────────────────────────────────────────
    RouteEntry(
        "docs",
        ("tạo tài liệu*", "viết tài liệu*", "tài liệu* cho"),
        ("docs*", "document*", "doc*", "readme*"),
    ),
    # ── Conversation / Ask (lowest priority — only when nothing else) ────
    RouteEntry(
        "ask",
        ("hỏi đáp*", "câu hỏi kiến trúc*"),
        ("question*", "architecture*", "how does*"),
    ),
]


# ── Matching engine ─────────────────────────────────────────────────────


def _matches(pattern: str, text: str) -> bool:
    """Return True if a user-facing keyword pattern matches *text*.

    Rules (applied in priority order):
    - trailing * (no prior space) → substring / phrase-prefix on the needle
    - otherwise → bare keyword must be a literal substring of *text*

    Matching is case-insensitive: both sides are lower-cased. Empty pattern
    or empty text never matches.
    """
    if not text or not text.strip():
        return False
    t = text.lower().strip()
    p = pattern.lower().strip()
    if not p:
        return False
    if p.endswith("*"):
        needle = p[:-1].rstrip()
        if not needle:
            return False
        return needle in t or t.startswith(needle + " ")
    return p in t


def match_routes(input_text: str) -> List[str]:
    """Return command names matched by *input_text*.

    First match per command wins; table order = priority. Empty inputs
    (``""``, ``None``, whitespace-only) yield ``[]``.
    """
    if not input_text or not input_text.strip():
        return []
    q = input_text.lower().strip()
    seen: set[str] = set()
    results: list[str] = []
    for entry in ROUTE_TABLE:
        if entry.command in seen:
            continue
        for kw in entry.vi_keywords + entry.en_keywords:
            if _matches(kw, q):
                results.append(entry.command)
                seen.add(entry.command)
                break
    return results


@dataclass
class CommandMatch:
    command: str
    score: float
    matched_pattern: str


def fuzzy_match(query: str, max_results: int = 5) -> List[CommandMatch]:
    """Return ranked ``CommandMatch`` results for interactive autocomplete.

    Scoring (applied to the *collapsed* keyword — starred suffix removed):
    - exact phrase     → 1.0
    - phrase prefix    → 0.8
    - substring hit    → 0.5
    Empty / whitespace-only queries return ``[]``. Max 5 results; tied
    scores preserve table order (first-tied kept).
    """
    if not query or not query.strip():
        return []
    q = query.lower().strip()
    seen: set[str] = set()
    results: list[CommandMatch] = []
    for entry in ROUTE_TABLE:
        if entry.command in seen:
            continue
        for kw in entry.vi_keywords + entry.en_keywords:
            kw_lower = kw.lower().strip()
            if _matches(kw_lower, q):
                needle = kw_lower.rstrip("*").rstrip()
                if not needle:
                    score = 0.5
                elif q == needle:
                    score = 1.0
                elif q.startswith(needle + " "):
                    score = 0.8
                else:
                    score = 0.5
                results.append(CommandMatch(entry.command, score, kw))
                seen.add(entry.command)
                break
    results.sort(key=_CommandMatch_sort_key, reverse=True)
    return results[:max_results]


def _CommandMatch_sort_key(m: CommandMatch) -> tuple:
    """Return a descending-sortable key that ties break by table order."""
    return (m.score,)


# ── Public API ─────────────────────────────────────────────────────────


def get_route_table() -> List[RouteEntry]:
    """Return full routing table (for iteration and external validation)."""
    return list(ROUTE_TABLE)


def get_all_commands() -> Tuple[str, ...]:
    """Return all registered command names in declaration order."""
    return tuple(e.command for e in ROUTE_TABLE)


__all__ = [
    "RouteEntry",
    "ROUTE_TABLE",
    "match_routes",
    "CommandMatch",
    "get_route_table",
    "get_all_commands",
    "fuzzy_match",
]
