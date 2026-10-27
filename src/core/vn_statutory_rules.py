# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Versioned Vietnamese statutory rule tables (jurisdiction = VN).

Every quantitative promise Mekong makes about tax, social insurance and
payroll is checked against an *independent* recomputation from these tables, so
a bug in an engine cannot silently pass verification (dual-path verification).

Rule versions are selected by the period they apply to, because Vietnamese tax
law changed while this repository was in development:

* PIT — Luật Thuế TNCN 2007 (7 brackets) with deductions per Nghị quyết
  954/2020/UBTVQH14 (11.0M / 4.4M) until 31/12/2025; Luật Thuế TNCN 2025
  (109/2025/QH15) reduces the schedule to 5 brackets and Nghị quyết
  110/2025/UBTVQH15 raises deductions to 15.5M / 6.2M from tax year 2026.
* CIT — Luật Thuế TNDN 2025 (67/2025/QH15, Điều 10) from 01/10/2025: 20%
  standard, 15% when annual revenue <= 3B VND, 17% for 3B < revenue <= 50B.
* BHXH — Luật BHXH 2024: ceiling = 20 x reference salary; reference salary
  2,340,000 (NĐ 73/2024) until 30/06/2026 and 2,530,000 (NĐ 161/2026) after.
  Regional minimum wages: NĐ 74/2024 until 31/12/2025, NĐ 293/2025 from
  01/01/2026 (BHTN ceiling = 20 x regional minimum wage).

Anything not covered here is *not* a legal guarantee: this is a rule table for
the operations Mekong advertises, with citations and effective dates attached.
"""

from __future__ import annotations

import dataclasses
import datetime
import decimal
import re
import typing
import unicodedata

D = decimal.Decimal
TODAY = datetime.date(2026, 10, 27)


def _d(value: typing.Any) -> D:
    return D(str(value))


def parse_date(value: typing.Any) -> datetime.date:
    """Accept ``date``, ISO string or ``YYYY-MM`` period labels."""
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    text = str(value or "").strip()
    if not text:
        return TODAY
    if len(text) == 7:  # YYYY-MM -> first day of the period
        text = f"{text}-01"
    if len(text) == 4:  # YYYY -> 1 July of that tax year (mid-year safe default)
        text = f"{text}-07-01"
    return datetime.date.fromisoformat(text)


@dataclasses.dataclass(frozen=True)
class RuleVersion:
    """One statutory rule set with its citation and validity window."""

    rule_id: str
    version: str
    citation: str
    effective_from: datetime.date
    effective_to: datetime.date | None
    params: typing.Mapping[str, typing.Any]

    def applies_to(self, as_of: datetime.date) -> bool:
        return as_of >= self.effective_from and (self.effective_to is None or as_of <= self.effective_to)

    def provenance(self) -> dict[str, typing.Any]:
        return {
            "rule_id": self.rule_id,
            "rule_version": self.version,
            "citation": self.citation,
            "effective_from": self.effective_from.isoformat(),
            "effective_to": self.effective_to.isoformat() if self.effective_to else None,
            "jurisdiction": "VN",
        }


# ---------------------------------------------------------------------------
# Personal income tax (Thuế TNCN) — progressive schedule on salary/wages
# ---------------------------------------------------------------------------

PIT_RULES: tuple[RuleVersion, ...] = (
    RuleVersion(
        "pit-salary", "2009-2020.06",
        "Luật Thuế TNCN 2007 (04/2007/QH12) Điều 22; Nghị quyết 948/2010/NQ-UBTVQH12",
        datetime.date(2009, 1, 1), datetime.date(2020, 6, 30),
        {
            "personal_deduction": _d(9_000_000),
            "dependent_deduction": _d(3_600_000),
            "brackets": ((5_000_000, "0.05"), (10_000_000, "0.10"), (18_000_000, "0.15"),
                         (32_000_000, "0.20"), (52_000_000, "0.25"), (80_000_000, "0.30"),
                         (None, "0.35")),
        },
    ),
    RuleVersion(
        "pit-salary", "2020.07-2025.12",
        "Luật Thuế TNCN 2007 Điều 22; Nghị quyết 954/2020/UBTVQH14 (giảm trừ gia cảnh)",
        datetime.date(2020, 7, 1), datetime.date(2025, 12, 31),
        {
            "personal_deduction": _d(11_000_000),
            "dependent_deduction": _d(4_400_000),
            "brackets": ((5_000_000, "0.05"), (10_000_000, "0.10"), (18_000_000, "0.15"),
                         (32_000_000, "0.20"), (52_000_000, "0.25"), (80_000_000, "0.30"),
                         (None, "0.35")),
        },
    ),
    RuleVersion(
        "pit-salary", "2026.01-luat-109/2025/QH15",
        "Luật Thuế TNCN 2025 (109/2025/QH15) Điều 9 (biểu thuế 5 bậc); "
        "Nghị quyết 110/2025/UBTVQH15 (giảm trừ 15,5 triệu / 6,2 triệu)",
        datetime.date(2026, 1, 1), None,
        {
            "personal_deduction": _d(15_500_000),
            "dependent_deduction": _d(6_200_000),
            "brackets": ((10_000_000, "0.05"), (30_000_000, "0.10"), (60_000_000, "0.20"),
                         (100_000_000, "0.30"), (None, "0.35")),
        },
    ),
)

# ---------------------------------------------------------------------------
# Corporate income tax (Thuế TNDN)
# ---------------------------------------------------------------------------

CIT_RULES: tuple[RuleVersion, ...] = (
    RuleVersion(
        "cit-rate", "2016-2025.09",
        "Luật Thuế TNDN 2008 (sửa đổi 2013, 2014) Điều 10 — thuế suất phổ thông 20%; "
        "Điều 10 Luật Hỗ trợ DNNVV 2017 nêu thuế suất ưu đãi 15%/17% nhưng các mức này chỉ "
        "được Luật Thuế TNDN 2025 (67/2025/QH15) bổ sung và áp dụng từ 01/10/2025",
        datetime.date(2016, 1, 1), datetime.date(2025, 9, 30),
        {"standard_rate": "0.20"},
    ),
    RuleVersion(
        "cit-rate", "luat-67/2025/QH15",
        "Luật Thuế TNDN 2025 (67/2025/QH15) Điều 10 khoản 1-3, hiệu lực 01/10/2025, "
        "áp dụng từ kỳ tính thuế năm 2025",
        datetime.date(2025, 10, 1), None,
        {"standard_rate": "0.20", "sme_small_rate": "0.15", "sme_small_max_revenue": _d(3_000_000_000),
         "sme_medium_rate": "0.17", "sme_medium_max_revenue": _d(50_000_000_000)},
    ),
)

# ---------------------------------------------------------------------------
# Social insurance (BHXH / BHYT / BHTN / KPCĐ)
# ---------------------------------------------------------------------------

BHXH_RULES: tuple[RuleVersion, ...] = (
    RuleVersion(
        "bhxh-contribution", "nd-73/2024",
        "Luật BHXH 2014; Nghị định 73/2024/NĐ-CP (lương cơ sở 2.340.000đ từ 01/07/2024); "
        "Nghị định 74/2024/NĐ-CP (lương tối thiểu vùng)",
        datetime.date(2024, 7, 1), datetime.date(2025, 12, 31),
        {
            "reference_salary": _d(2_340_000), "ceiling_multiplier": _d(20),
            "regional_min_wage": {1: _d(4_960_000), 2: _d(4_410_000), 3: _d(3_860_000), 4: _d(3_450_000)},
            "employee_rates": {"bhxh": "0.08", "bhyt": "0.015", "bhtn": "0.01"},
            "employer_rates": {"bhxh": "0.175", "bhyt": "0.03", "bhtn": "0.01", "kpcd": "0.02"},
        },
    ),
    RuleVersion(
        "bhxh-contribution", "luat-bhxh-2024_nd-293/2025",
        "Luật BHXH 2024 (41/2024/QH15) Điều 31; Nghị định 293/2025/NĐ-CP "
        "(lương tối thiểu vùng từ 01/01/2026)",
        datetime.date(2026, 1, 1), datetime.date(2026, 6, 30),
        {
            "reference_salary": _d(2_340_000), "ceiling_multiplier": _d(20),
            "regional_min_wage": {1: _d(5_310_000), 2: _d(4_730_000), 3: _d(4_140_000), 4: _d(3_700_000)},
            "employee_rates": {"bhxh": "0.08", "bhyt": "0.015", "bhtn": "0.01"},
            "employer_rates": {"bhxh": "0.175", "bhyt": "0.03", "bhtn": "0.01", "kpcd": "0.02"},
        },
    ),
    RuleVersion(
        "bhxh-contribution", "nd-161/2026",
        "Nghị định 161/2026/NĐ-CP (lương cơ sở 2.530.000đ từ 01/07/2026); "
        "Luật BHXH 2024 Điều 31 (trần 20 lần mức tham chiếu)",
        datetime.date(2026, 7, 1), None,
        {
            "reference_salary": _d(2_530_000), "ceiling_multiplier": _d(20),
            "regional_min_wage": {1: _d(5_310_000), 2: _d(4_730_000), 3: _d(4_140_000), 4: _d(3_700_000)},
            "employee_rates": {"bhxh": "0.08", "bhyt": "0.015", "bhtn": "0.01"},
            "employer_rates": {"bhxh": "0.175", "bhyt": "0.03", "bhtn": "0.01", "kpcd": "0.02"},
        },
    ),
)

# ---------------------------------------------------------------------------
# Value added tax (Thuế GTGT) — Luật GTGT 2024 + the 2% reduction window
# ---------------------------------------------------------------------------

#: Sectors excluded from the 10% -> 8% reduction (Nghị quyết 204/2025/QH15 Điều 1
#: khoản 1; Nghị định 174/2025/NĐ-CP Phụ lục I). Keys are the ASCII-folded,
#: hyphenated form produced by :func:`fold_sector` so that both the Vietnamese
#: legal wording and the English shorthand match.
VAT_REDUCTION_EXCLUDED_SECTORS: frozenset[str] = frozenset({
    # viễn thông (telecommunications)
    "telecom", "telecommunications", "vien-thong", "buu-chinh-vien-thong",
    "dich-vu-vien-thong", "cong-nghe-vien-thong",
    # tài chính, ngân hàng, chứng khoán, bảo hiểm
    "finance", "financial-services", "tai-chinh", "dich-vu-tai-chinh",
    "banking", "ngan-hang", "tin-dung", "dich-vu-ngan-hang",
    "securities", "chung-khoan", "chungkhoan", "kinh-doanh-chung-khoan",
    "insurance", "bao-hiem", "baohiem", "kinh-doanh-bao-hiem",
    # kinh doanh bất động sản
    "real-estate", "real estate", "bat-dong-san", "batdongsan",
    "kinh-doanh-bat-dong-san",
    # kim loại và sản phẩm từ kim loại đúc sẵn
    "metal-products", "kim-loai", "kimloai", "san-pham-kim-loai",
    "san-pham-tu-kim-loai-duc-san",
    # khai khoáng (trừ khai thác than)
    "mining", "khai-khoang", "khaikhoang", "khoang-san", "khai-thac-khoang-san",
    # hàng hoá chịu thuế tiêu thụ đặc biệt (trừ xăng)
    "excise-goods", "thue-tieu-thu-dac-biet", "hang-chiu-thue-tieu-thu-dac-biet",
    "thuoc-la", "ruou", "bia", "oto-duoi-24-cho",
})

#: Sub-sectors explicitly *kept* at the reduced rate inside the window.
VAT_REDUCTION_EXCEPTIONS: frozenset[str] = frozenset({
    "than", "khai-thac-than", "coal", "xang", "gasoline", "dau-nhon",
})


def fold_sector(sector: typing.Any) -> str:
    """Fold a sector name to the ASCII, hyphenated key used by the exclusion set."""
    text = unicodedata.normalize("NFKD", str(sector or "").strip().lower())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    # 'đ' has no NFKD decomposition, so it must be folded explicitly.
    text = text.replace("\u0111", "d").replace("\u0110", "d")
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text

VAT_RULES: tuple[RuleVersion, ...] = (
    RuleVersion(
        "vat-gtgt", "luat-gtgt-2008",
        "Luật Thuế GTGT 2008 (13/2008/QH12, sửa đổi 2013/2016) Điều 8; NĐ 123/2020/NĐ-CP, TT 78/2021/TT-BTC",
        datetime.date(2009, 1, 1), datetime.date(2025, 6, 30),
        {"rates": (0, 5, 10), "reduced_rate": None},
    ),
    RuleVersion(
        "vat-gtgt", "luat-gtgt-2024_48/2024/QH15",
        "Luật Thuế GTGT 2024 (48/2024/QH15) Điều 8-9, hiệu lực 01/07/2025; "
        "NĐ 180/2024/NĐ-CP (giảm 2% đến 30/06/2025)",
        datetime.date(2025, 1, 1), datetime.date(2025, 6, 30),
        {"rates": (0, 5, 8, 10), "reduced_rate": 8},
    ),
    RuleVersion(
        "vat-gtgt", "luat-gtgt-2024 + nq-204/2025/QH15",
        "Luật Thuế GTGT 2024 (48/2024/QH15) Điều 9 khoản 3; Nghị quyết 204/2025/QH15 "
        "và Nghị định 174/2025/NĐ-CP — giảm 10% xuống 8% từ 01/07/2025 đến hết 31/12/2026",
        datetime.date(2025, 7, 1), datetime.date(2026, 12, 31),
        {"rates": (0, 5, 8, 10), "reduced_rate": 8,
         "reduction_excluded_sectors": sorted(VAT_REDUCTION_EXCLUDED_SECTORS)},
    ),
    RuleVersion(
        "vat-gtgt", "luat-gtgt-2024 (sau giai đoạn giảm thuế)",
        "Luật Thuế GTGT 2024 (48/2024/QH15) Điều 8 — thuế suất phổ thông 10% sau 31/12/2026",
        datetime.date(2027, 1, 1), None,
        {"rates": (0, 5, 10), "reduced_rate": None},
    ),
)


def vat_rule(as_of: typing.Any = None) -> RuleVersion:
    return pick(VAT_RULES, as_of)


def validate_vat_rate(
    rate: typing.Any,
    as_of: typing.Any = None,
    *,
    sector: str | None = None,
) -> dict[str, typing.Any]:
    """Check that a requested VAT rate is legal for the period and sector."""
    rule = vat_rule(as_of)
    allowed = tuple(rule.params["rates"])  # type: ignore[index]
    try:
        rate_value = int(float(str(rate)))
    except (TypeError, ValueError):
        return {"valid": False, "reason": f"VAT rate '{rate}' is not a number", **rule.provenance()}
    if rate_value not in allowed:
        return {
            "valid": False,
            "reason": f"VAT rate {rate_value}% is not statutory for this period (allowed: {list(allowed)})",
            **rule.provenance(),
        }
    if rate_value == 8 and sector:
        normalized = fold_sector(sector)
        excluded = set(rule.params.get("reduction_excluded_sectors") or ())  # type: ignore[union-attr]
        tokens = {normalized, *normalized.split("-")}
        # "khai thác than" and "xăng" stay eligible even though mining and
        # excise-duty goods as a whole are excluded.
        exception_hit = bool(tokens & VAT_REDUCTION_EXCEPTIONS)
        if not exception_hit and (normalized in excluded or normalized in VAT_REDUCTION_EXCLUDED_SECTORS):
            return {
                "valid": False,
                "reason": (
                    f"sector '{sector}' is excluded from the 10%->8% reduction "
                    "(Nghị quyết 204/2025/QH15 Điều 1 khoản 1)"
                ),
                **rule.provenance(),
            }
    return {"valid": True, "rate": rate_value, **rule.provenance()}


MST_CHECKSUM_WEIGHTS: tuple[int, ...] = (31, 29, 23, 19, 17, 13, 7, 5, 3)
MST_CITATION = (
    "Điều 5 Thông tư 105/2020/TT-BTC / Điều 30 Luật Quản lý thuế 2019 (38/2019/QH14); "
    "chữ số thứ 10 là số kiểm tra modulus 11 với trọng số 31,29,23,19,17,13,7,5,3"
)


def pick(rules: tuple[RuleVersion, ...], as_of: typing.Any) -> RuleVersion:
    date = parse_date(as_of)
    for rule in rules:
        if rule.applies_to(date):
            return rule
    # Before the earliest known version: fall back to the earliest and say so.
    return min(rules, key=lambda r: r.effective_from)


def pit_rule(as_of: typing.Any = None) -> RuleVersion:
    return pick(PIT_RULES, as_of)


def cit_rule(as_of: typing.Any = None) -> RuleVersion:
    return pick(CIT_RULES, as_of)


def bhxh_rule(as_of: typing.Any = None) -> RuleVersion:
    return pick(BHXH_RULES, as_of)


# ---------------------------------------------------------------------------
# Independent recomputations (used by postcondition verifiers)
# ---------------------------------------------------------------------------

def compute_pit(taxable_income: typing.Any, as_of: typing.Any = None) -> dict[str, typing.Any]:
    """Progressive PIT on monthly taxable income for the given period."""
    rule = pit_rule(as_of)
    income = max(_d(0), _d(taxable_income))
    tax = _d(0)
    breakdown: list[dict[str, typing.Any]] = []
    lower = _d(0)
    for ceiling, rate in rule.params["brackets"]:  # type: ignore[index]
        upper = _d(ceiling) if ceiling is not None else None
        if upper is None or income > lower:
            band_end = income if upper is None else min(income, upper)
            band = max(_d(0), band_end - lower)
            amount = (band * _d(rate)).quantize(_d(1), rounding=decimal.ROUND_HALF_UP)
            if band > 0:
                breakdown.append({"from": float(lower), "to": float(band_end),
                                  "rate_pct": float(_d(rate) * 100), "tax": float(amount)})
            tax += amount
            if upper is None:
                break
            lower = upper
        else:
            break
    return {"tax": float(tax), "breakdown": breakdown, **rule.provenance()}


def compute_deductions(dependents: int, as_of: typing.Any = None) -> dict[str, typing.Any]:
    rule = pit_rule(as_of)
    personal = _d(rule.params["personal_deduction"])  # type: ignore[index]
    per_dependent = _d(rule.params["dependent_deduction"])  # type: ignore[index]
    return {
        "personal_deduction": float(personal),
        "dependent_deduction": float(per_dependent * _d(int(dependents))),
        "total_deductions": float(personal + per_dependent * _d(int(dependents))),
        **rule.provenance(),
    }


def compute_cit(
    taxable_profit: typing.Any,
    annual_revenue: typing.Any,
    as_of: typing.Any = None,
    *,
    is_sme: bool = True,
) -> dict[str, typing.Any]:
    """CIT for a tax year, applying the revenue-based SME rates of Điều 10."""
    rule = cit_rule(as_of)
    profit = max(_d(0), _d(taxable_profit))
    revenue = _d(annual_revenue)
    # A rule version without SME tiers (before 01/10/2025) always yields the
    # standard rate — the preferential tiers must not be applied retroactively.
    small_rate = rule.params.get("sme_small_rate")  # type: ignore[union-attr]
    medium_rate = rule.params.get("sme_medium_rate")  # type: ignore[union-attr]
    small_max = _d(rule.params.get("sme_small_max_revenue", _d(0)))  # type: ignore[union-attr]
    medium_max = _d(rule.params.get("sme_medium_max_revenue", _d(0)))  # type: ignore[union-attr]
    if is_sme and small_rate is not None and revenue <= small_max:
        rate, tier = _d(small_rate), "SME_SMALL_15"
    elif is_sme and medium_rate is not None and revenue <= medium_max:
        rate, tier = _d(medium_rate), "SME_MEDIUM_17"
    else:
        rate, tier = _d(rule.params["standard_rate"]), "STANDARD_20"  # type: ignore[index]
    tax = (profit * rate).quantize(_d(1), rounding=decimal.ROUND_HALF_UP)
    return {"tax": float(tax), "rate_pct": float(rate * 100), "rate_tier": tier,
            "net_profit": float(profit - tax), **rule.provenance()}


def compute_bhxh(
    salary: typing.Any,
    region: int = 1,
    as_of: typing.Any = None,
    *,
    include_kpcd: bool = False,
) -> dict[str, typing.Any]:
    """Employee/employer contributions with statutory ceilings."""
    rule = bhxh_rule(as_of)
    gross = max(_d(0), _d(salary))
    reference = _d(rule.params["reference_salary"])  # type: ignore[index]
    multiplier = _d(rule.params["ceiling_multiplier"])  # type: ignore[index]
    regional = _d(rule.params["regional_min_wage"][int(region)])  # type: ignore[index]
    ceiling_social = reference * multiplier
    ceiling_unemployment = regional * multiplier
    base_social = min(gross, ceiling_social)
    base_unemployment = min(gross, ceiling_unemployment)
    emp_rates = rule.params["employee_rates"]  # type: ignore[index]
    emp_rates = {k: _d(v) for k, v in emp_rates.items()}  # type: ignore[union-attr]
    em_rates = rule.params["employer_rates"]  # type: ignore[index]
    em_rates = {k: _d(v) for k, v in em_rates.items()}  # type: ignore[union-attr]

    def _money(value: D) -> D:
        return value.quantize(_d(1), rounding=decimal.ROUND_HALF_UP)

    employee = {
        "bhxh": _money(base_social * emp_rates["bhxh"]),
        "bhyt": _money(base_social * emp_rates["bhyt"]),
        "bhtn": _money(base_unemployment * emp_rates["bhtn"]),
    }
    employer = {
        "bhxh": _money(base_social * em_rates["bhxh"]),
        "bhyt": _money(base_social * em_rates["bhyt"]),
        "bhtn": _money(base_unemployment * em_rates["bhtn"]),
        "kpcd": _money(base_social * em_rates["kpcd"]) if include_kpcd else _d(0),
    }
    return {
        "employee": {k: float(v) for k, v in employee.items()},
        "employer": {k: float(v) for k, v in employer.items()},
        "employee_total": float(sum(employee.values())),
        "employer_total": float(sum(employer.values())),
        "total_contribution": float(sum(employee.values()) + sum(employer.values())),
        "ceiling_bhxh_bhyt": float(ceiling_social),
        "ceiling_bhtn": float(ceiling_unemployment),
        "base_bhxh_bhyt": float(base_social),
        "base_bhtn": float(base_unemployment),
        "is_capped": bool(gross > ceiling_social or gross > ceiling_unemployment),
        **rule.provenance(),
    }


def mst_checksum(tax_code: str) -> dict[str, typing.Any]:
    """Independent MST (mã số thuế) check-digit validation, modulus 11."""
    code = str(tax_code or "").strip().replace("-", "").replace(" ", "")
    if not code.isdigit() or len(code) not in (10, 13):
        return {"valid": False, "reason": "MST must be 10 or 13 digits", "citation": MST_CITATION}
    base = code[:10]
    total = sum(w * int(digit) for w, digit in zip(MST_CHECKSUM_WEIGHTS, base[:9]))
    remainder = total % 11
    expected = 10 - remainder
    if expected == 10:
        expected = 0
    actual = int(base[9])
    valid = expected == actual
    return {
        "valid": valid,
        "expected_check_digit": expected,
        "actual_check_digit": actual,
        "reason": None if valid else "check digit does not match modulus-11 computation",
        "citation": MST_CITATION,
    }


def vat_amount(
    subtotal: typing.Any,
    rate_pct: typing.Any,
    as_of: typing.Any = None,
    *,
    sector: str | None = None,
) -> dict[str, typing.Any]:
    """Independent VAT recomputation with period/sector legality check."""
    legality = validate_vat_rate(rate_pct, as_of, sector=sector)
    base = _d(subtotal)
    rate = _d(rate_pct)
    vat = (base * rate / _d(100)).quantize(_d(1), rounding=decimal.ROUND_HALF_UP)
    return {"vat": float(vat), "total_inclusive": float(base + vat), "rate_valid": legality["valid"],
            "rate_legality": legality, "jurisdiction": "VN",
            "rule_id": legality["rule_id"], "rule_version": legality["rule_version"],
            "citation": legality["citation"]}


__all__ = [
    "BHXH_RULES",
    "CIT_RULES",
    "MST_CHECKSUM_WEIGHTS",
    "MST_CITATION",
    "PIT_RULES",
    "TODAY",
    "VAT_REDUCTION_EXCEPTIONS",
    "VAT_REDUCTION_EXCLUDED_SECTORS",
    "VAT_RULES",
    "RuleVersion",
    "bhxh_rule",
    "cit_rule",
    "compute_bhxh",
    "compute_cit",
    "compute_deductions",
    "compute_pit",
    "fold_sector",
    "mst_checksum",
    "parse_date",
    "pick",
    "pit_rule",
    "validate_vat_rate",
    "vat_amount",
    "vat_rule",
]
