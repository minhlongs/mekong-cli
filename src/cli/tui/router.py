"""NL router stubs for tests - kept in sync with cli/tui/router.py."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class RouteEntry:
    """One entry in the route table."""
    command: str
    vi_keywords: Tuple[str, ...] = field(default_factory=tuple)
    en_keywords: Tuple[str, ...] = field(default_factory=tuple)
    description: str = ""


@dataclass
class CommandMatch:
    """A match result from fuzzy matching."""
    command: str
    score: float
    matched_keyword: str = ""


ROUTE_TABLE: List[RouteEntry] = [
    RouteEntry(command="fix", vi_keywords=("sửa lỗi*", "sửa bug*", "sửa", "lỗi*"), en_keywords=("fix*", "debug*", "bug*", "broken*"), description="Fix command"),
    RouteEntry(command="plan", vi_keywords=("lập kế hoạch*", "lên kế hoạch*", "tạo kế hoạch*", "kế hoạch*", "plan*"), en_keywords=("plan*", "create plan*", "build plan*"), description="Plan command"),
    RouteEntry(command="content-blog", vi_keywords=("viết blog*", "viết bài blog*", "bài viết*"), en_keywords=("write blog*", "write a blog*", "blog post*"), description="Content blog command"),
    RouteEntry(command="marketing-campaign", vi_keywords=("chiến dịch*", "tạo chiến dịch*", "lập chiến dịch*"), en_keywords=("build a campaign*", "create a campaign*", "marketing campaign*"), description="Marketing campaign command"),
    RouteEntry(command="security-scan", vi_keywords=("quét bảo mật*", "kiểm tra bảo mật*"), en_keywords=("security scan*", "security audit*"), description="Security scan command"),
    RouteEntry(command="analytics-report", vi_keywords=("phân tích dữ liệu*", "phân tích data*", "báo cáo phân tích*"), en_keywords=("view analytics*", "analyze data*", "analytics*"), description="Analytics report command"),
    RouteEntry(command="deploy", vi_keywords=("triển khai*", "đưa lên production*", "deploy*"), en_keywords=("deploy*", "push to prod*", "go live*"), description="Deploy command"),
    RouteEntry(command="docs", vi_keywords=("tạo tài liệu*", "viết tài liệu*"), en_keywords=("docs*", "document*", "readme*"), description="Docs command"),
    RouteEntry(command="cook", vi_keywords=("code*", "viết code*", "code giao diện", "lập trình*"), en_keywords=("code*", "implement*", "develop*", "build*", "write code*"), description="Cook command"),
    RouteEntry(command="debug", vi_keywords=("debug*", "gỡ lỗi*", "sửa bug*"), en_keywords=("debug*", "fix*"), description="Debug command"),
]


def _matches(pattern: str, text: str) -> bool:
    p = pattern.lower()
    t = text.lower()
    if p.endswith("*"):
        return t.startswith(p[:-1])
    return p in t


def fuzzy_match(pattern: str, text: str) -> Optional[CommandMatch]:
    if _matches(pattern, text):
        return CommandMatch(command=pattern, score=0.5, matched_keyword=pattern)
    return None


def get_route_table() -> List[RouteEntry]:
    return ROUTE_TABLE


def get_all_commands() -> List[str]:
    return [e.command for e in ROUTE_TABLE]


def match_routes(query: str) -> List[str]:
    matches: List[str] = []
    for entry in ROUTE_TABLE:
        for kw in entry.vi_keywords + entry.en_keywords:
            if _matches(kw, query):
                matches.append(entry.command)
                break
    return matches


def route_ask(input_text: str) -> Optional[str]:
    matches = match_routes(input_text)
    if not matches:
        return None
    if len(matches) == 1:
        return matches[0]
    # Multiple matches — pick the one whose first keyword is longest
    best = None
    best_len = -1
    for cmd in matches:
        for entry in ROUTE_TABLE:
            if entry.command == cmd:
                # Use combined keywords, get the first one
                all_kws = entry.vi_keywords + entry.en_keywords
                first_kw = all_kws[0] if all_kws else ""
                kw_len = len(first_kw.rstrip("*"))
                if kw_len > best_len:
                    best = cmd
                    best_len = kw_len
                break
    return best