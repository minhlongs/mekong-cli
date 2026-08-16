# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Spec-kit multi-artifact templates.

Renders supplementary SDD artifacts after plan generation:
  - data-model.md  — entity list + relationships
  - quickstart.md  — local setup instructions
  - research.md    — AI research placeholder
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Language labels
# ---------------------------------------------------------------------------

_LABELS = {
    "en": {
        "dm_title": "## Data Model\n",
        "dm_entities": "### Entities\n\n",
        "dm_relationships": "### Relationships\n\n",
        "dm_diagram": "### ER Diagram (text)\n\n```\n",
        "qs_title": "## Quickstart\n",
        "qs_prereq": "### Prerequisites\n\n",
        "qs_steps": "### Setup Steps\n\n",
        "qs_verify": "### Verify\n\n",
        "research_title": "## Research\n",
        "research_intro": "> AI-researched context. Fill before implementation.\n\n",
        "research_tech": "### Tech Stack Evaluation\n\n",
        "research_competitors": "### Competitive Landscape\n\n",
        "research_architecture": "### Architecture Decisions\n\n",
    },
    "vi": {
        "dm_title": "## Mô hình dữ liệu\n",
        "dm_entities": "### Thực thể\n\n",
        "dm_relationships": "### Mối quan hệ\n\n",
        "dm_diagram": "### Sơ đồ ER (text)\n\n```\n",
        "qs_title": "## Khởi động nhanh\n",
        "qs_prereq": "### Điều kiện tiên quyết\n\n",
        "qs_steps": "### Các bước cài đặt\n\n",
        "qs_verify": "### Xác minh\n\n",
        "research_title": "## Nghiên cứu\n",
        "research_intro": "> Ngữ cảnh nghiên cứu AI. Điền trước khi triển khai.\n\n",
        "research_tech": "### Đánh giá Công nghệ\n\n",
        "research_competitors": "### Bối cảnh Cạnh tranh\n\n",
        "research_architecture": "### Quyết định Kiến trúc\n\n",
    },
}


def _l(lang: str) -> dict[str, str]:
    return _LABELS.get(lang, _LABELS["en"])


# ---------------------------------------------------------------------------
# Public render functions
# ---------------------------------------------------------------------------


def render_data_model(company: dict, lang: str) -> str:
    entities = company.get("entities") or _default_entities(company)
    lines: list[str] = []
    lb = _l(lang)

    lines.append(lb["dm_title"])
    lines.append(lb["dm_entities"])

    for ent in entities:
        lines.append(f"#### {ent['name']}\n")
        for fld in ent.get("fields", []):
            lines.append(f"- `{fld}`")
        lines.append("")

    lines.append(lb["dm_relationships"])
    for rel in _default_relationships():
        lines.append(f"- {rel}")
    lines.append("")

    lines.append(lb["dm_diagram"])
    for e in entities:
        lines.append(f"  [{e['name']}]")
    lines.append("```\n")

    return "\n".join(lines)


def render_quickstart(company: dict, lang: str) -> str:
    lines: list[str] = []
    lb = _l(lang)
    is_en = lang == "en"

    lines.append(lb["qs_title"])
    lines.append(lb["qs_prereq"])
    lines.append("- Python 3.11+" if is_en else "- Python 3.11+")
    lines.append("- Node.js 20+ (frontend)" if is_en else "- Node.js 20+ (frontend)")
    lines.append("- Cloudflare account (Wrangler)" if is_en else "- Tài khoản Cloudflare (Wrangler)")
    lines.append("")

    lines.append(lb["qs_steps"])
    steps = (
        [
            "1. Clone repo & enter project",
            "2. Copy `.env.example` → `.env`; fill secrets",
            "3. `npm install` (root + app)",
            "4. `npx wrangler d1 create <db>` — copy DB ID",
            "5. Apply migrations: `bash scripts/apply-migrations.sh`",
            "6. `npm run dev` — confirm `localhost:3000`",
        ]
        if is_en
        else [
            "1. Clone repo & vào project",
            "2. Copy `.env.example` → `.env`; điền secrets",
            "3. `npm install` (root + app)",
            "4. `npx wrangler d1 create <db>` — copy DB ID",
            "5. Apply migrations: `bash scripts/apply-migrations.sh`",
            "6. `npm run dev` — xác nhận `localhost:3000`",
        ]
    )
    lines.extend(f"{s}\n" for s in steps)

    lines.append(lb["qs_verify"])
    lines.append("`npm run build && npm test`\n" if is_en else "`npm run build && npm test`\n")

    return "\n".join(lines)


def render_research(company: dict, lang: str) -> str:
    lines: list[str] = []
    lb = _l(lang)
    is_en = lang == "en"

    lines.append(lb["research_title"])
    lines.append(lb["research_intro"])

    sections = [
        (lb["research_tech"], "Stack comparison, library evaluation, API trade-offs."),
        (lb["research_competitors"], "Market alternatives, positioning gap analysis."),
        (lb["research_architecture"], "Pattern selection, scalability, security model."),
    ]
    for heading, placeholder in sections:
        lines.append(heading)
        lines.append(
            f"{placeholder}\n" if is_en else f"{placeholder}\n"
        )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Defaults (when company.json lacks custom entity list)
# ---------------------------------------------------------------------------


def _default_entities(company: dict) -> list[dict]:
    ptype = company.get("product_type", "saas")
    if ptype in ("saas", "api_service"):
        return [
            {"name": "User", "fields": ["id: uuid", "email: str", "tier: enum", "created_at: datetime"]},
            {"name": "Subscription", "fields": ["id: uuid", "user_id: uuid", "status: enum", "ends_at: datetime"]},
            {"name": "UsageEvent", "fields": ["id: uuid", "user_id: uuid", "command: str", "credits: int"]},
        ]
    if ptype == "ecommerce":
        return [
            {"name": "Product", "fields": ["id: uuid", "name: str", "price: decimal", "stock: int"]},
            {"name": "Order", "fields": ["id: uuid", "user_id: uuid", "total: decimal", "status: enum"]},
            {"name": "OrderItem", "fields": ["id: uuid", "order_id: uuid", "product_id: uuid", "qty: int"]},
        ]
    return [
        {"name": "Entity", "fields": ["id: uuid", "name: str", "created_at: datetime"]},
    ]


def _default_relationships() -> list[str]:
    return [
        "User 1:N Subscription",
        "User 1:N UsageEvent",
        "Subscription 1:N Invoice",
    ]
