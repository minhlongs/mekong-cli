"""Tests for the i18n module (src/cli/commands/company_init/i18n.py).

Covers:
1. All PROMPT_EN keys have non-empty values
2. All PROMPT_VI keys have non-empty values (no "[VI TBD]" sentinels)
3. PROMPT_EN and PROMPT_VI share the same key set
4. t() helper resolves correctly for 'en' and 'vi'
5. t() falls back to default (then English) when key is missing
6. Spot-checks on 5 specific translations for quality
7. Legacy alias keys (q1_name, q2_prompt, etc.) resolve correctly
"""

from __future__ import annotations

import os
import sys

import pytest

# Ensure src/ is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.cli.commands.company_init.i18n import (  # noqa: E402
    PROMPT_EN,
    PROMPT_VI,
    DEFAULT_LOCALE,
    MESSAGES,
    get_messages,
    t,
)


# ── Helpers ─────────────────────────────────────────────────────────────────


def _vi_tbd(text: str) -> bool:
    """Return True if the string contains an untranslated sentinel."""
    return "[VI TBD" in text


# ── Fixtures / Shared data ──────────────────────────────────────────────────


@pytest.fixture()
def all_en_keys():
    return set(PROMPT_EN.keys())


@pytest.fixture()
def all_vi_keys():
    return set(PROMPT_VI.keys())


# ── 1. PROMPT_EN: every key has a non-empty value ───────────────────────────


class TestPromptEnNonEmpty:
    def test_all_values_non_empty(self) -> None:
        empty = {k: v for k, v in PROMPT_EN.items() if not v or not v.strip()}
        assert not empty, f"PROMPT_EN has empty values for keys: {empty.keys()}"

    def test_value_types_are_strings(self) -> None:
        bad = {k: type(v).__name__ for k, v in PROMPT_EN.items() if not isinstance(v, str)}
        assert not bad, f"PROMPT_EN has non-string values: {bad}"


# ── 2. PROMPT_VI: no untranslated sentinels remain ──────────────────────────


class TestPromptViComplete:
    def test_no_vi_tbd_sentinels(self) -> None:
        tbd = {k: v for k, v in PROMPT_VI.items() if _vi_tbd(v)}
        assert not tbd, (
            f"PROMPT_VI still has untranslated entries: "
            f"{ {k: v[:60] for k, v in tbd.items()} }"
        )

    def test_all_values_non_empty(self) -> None:
        empty = {k: v for k, v in PROMPT_VI.items() if not v or not v.strip()}
        assert not empty, f"PROMPT_VI has empty values for keys: {empty.keys()}"

    def test_value_types_are_strings(self) -> None:
        bad = {k: type(v).__name__ for k, v in PROMPT_VI.items() if not isinstance(v, str)}
        assert not bad, f"PROMPT_VI has non-string values: {bad}"


# ── 3. PROMPT_EN keys match PROMPT_VI keys ──────────────────────────────────


class TestKeyParity:
    def test_same_keys_en_in_vi(self) -> None:
        extra_vi = set(PROMPT_VI.keys()) - set(PROMPT_EN.keys())
        assert not extra_vi, f"PROMPT_VI has keys not in PROMPT_EN: {extra_vi}"

    def test_same_keys_vi_in_en(self) -> None:
        extra_en = set(PROMPT_EN.keys()) - set(PROMPT_VI.keys())
        assert not extra_en, f"PROMPT_EN has keys not in PROMPT_VI: {extra_en}"

    def test_key_count_matches(self) -> None:
        assert len(PROMPT_EN) == len(PROMPT_VI), (
            f"Key count mismatch: EN={len(PROMPT_EN)}, VI={len(PROMPT_VI)}"
        )


# ── 4. t() helper: correct resolution for 'en' and 'vi' ────────────────────


class TestTHelper:
    @pytest.mark.parametrize("locale", ["en", "vi"])
    def test_t_returns_non_empty_for_known_key(self, locale: str) -> None:
        value = t(locale, "welcome")
        assert value, f"t('{locale}', 'welcome') returned empty"
        assert isinstance(value, str)

    def test_t_en_welcome_matches_prompt_en(self) -> None:
        assert t("en", "welcome") == PROMPT_EN["welcome"]

    def test_t_vi_welcome_matches_prompt_vi(self) -> None:
        assert t("vi", "welcome") == PROMPT_VI["welcome"]

    @pytest.mark.parametrize("key", ["q1_company_name", "q2_header", "q3_scenario"])
    def test_t_resolves_multiple_keys_en(self, key: str) -> None:
        assert t("en", key) == PROMPT_EN[key]

    @pytest.mark.parametrize("key", ["q1_company_name", "q2_header", "q3_scenario"])
    def test_t_resolves_multiple_keys_vi(self, key: str) -> None:
        assert t("vi", key) == PROMPT_VI[key]


# ── 5. t() fallback: default → English when key not found ───────────────────


class TestTFallback:
    def test_missing_key_returns_empty_default(self) -> None:
        assert t("en", "nonexistent_key_xyz", default="") == ""

    def test_missing_key_returns_custom_default(self) -> None:
        assert t("en", "nonexistent_key_xyz", default="fallback_text") == "fallback_text"

    def test_missing_key_in_vi_falls_back_to_english(self) -> None:
        result = t("vi", "nonexistent_key_abc")
        # Key is in neither locale → falls through to default ("")
        assert result == ""

    def test_missing_key_in_en_falls_back_to_english(self) -> None:
        result = t("en", "nonexistent_key_abc")
        # Key exists in vi but not en — t should try English, fail, return ""
        assert result == ""

    def test_unknown_locale_falls_back_to_english(self) -> None:
        # 'fr' is not in MESSAGES — get_messages falls back to DEFAULT_LOCALE
        result = t("fr", "welcome")
        assert result == PROMPT_EN["welcome"]


# ── 6. Spot-check: 5 specific translations for quality ─────────────────────


class TestTranslationQuality:
    # Key 1: wizard entry point — must not be placeholder
    def test_welcome_translated(self) -> None:
        vi_val = PROMPT_VI["welcome"]
        assert not _vi_tbd(vi_val), "'welcome' is still untranslated"
        assert len(vi_val) > 2, "'welcome' translation is suspiciously short"
        assert "Mekong" in vi_val, "'welcome' should mention Mekong"

    # Key 2: company name prompt — core input field
    def test_q1_company_name_translated(self) -> None:
        en = PROMPT_EN["q1_company_name"]
        vi = PROMPT_VI["q1_company_name"]
        assert en != vi, "VI should not be identical to EN (untranslated)"
        assert not _vi_tbd(vi), "'q1_company_name' is still untranslated"
        assert "tên" in vi.lower() or "công ty" in vi.lower(), (
            "VI translation should contain natural Vietnamese words for company name"
        )

    # Key 3: reset confirmation — critical warning
    def test_reset_confirm_translated(self) -> None:
        vi_val = PROMPT_VI["reset_confirm"]
        assert not _vi_tbd(vi_val), "'reset_confirm' is still untranslated"
        assert len(vi_val) > 10, "'reset_confirm' should be a full sentence"
        assert "XÓA" in vi_val or "xóa" in vi_val.lower(), (
            "'reset_confirm' should mention the destructive action (XÓA)"
        )

    # Key 4: status header — used in display
    def test_company_status_translated(self) -> None:
        en = PROMPT_EN["company_status"]
        vi = PROMPT_VI["company_status"]
        assert not _vi_tbd(vi), "'company_status' is still untranslated"
        assert en != vi, "VI should differ from EN"
        assert len(vi) > 1, "'company_status' translation is empty"

    # Key 5: error message — user-visible error path
    def test_error_generic_translated(self) -> None:
        en = PROMPT_EN["error_generic"]
        vi = PROMPT_VI["error_generic"]
        assert not _vi_tbd(vi), "'error_generic' is still untranslated"
        assert en != vi, "VI should differ from EN"
        assert "thất bại" in vi.lower() or "lỗi" in vi.lower(), (
            "'error_generic' should contain Vietnamese error wording"
        )


# ── 7. Legacy alias keys resolve correctly ─────────────────────────────────


class TestLegacyAliases:
    # These are the compat aliases documented in the module docstring
    ALIASES = [
        "q1_name",      # alias for q1_company_name
        "q2_prompt",    # alias for q2_product_type
        "q3_prompt",    # alias for q3_scenario
        "q4_prompt",    # alias for q4_budget
        "q5_prompt",    # alias for q5_language
        "error",        # alias for error_generic
    ]

    @pytest.mark.parametrize("key", ALIASES)
    def test_alias_exists_in_en(self, key: str) -> None:
        assert key in PROMPT_EN, f"Legacy alias '{key}' missing from PROMPT_EN"

    @pytest.mark.parametrize("key", ALIASES)
    def test_alias_exists_in_vi(self, key: str) -> None:
        assert key in PROMPT_VI, f"Legacy alias '{key}' missing from PROMPT_VI"

    @pytest.mark.parametrize("key", ALIASES)
    def test_alias_resolves_via_t_en(self, key: str) -> None:
        result = t("en", key)
        assert result, f"t('en', '{key}') returned empty"
        assert _vi_tbd(result) is False

    @pytest.mark.parametrize("key", ALIASES)
    def test_alias_resolves_via_t_vi(self, key: str) -> None:
        result = t("vi", key)
        assert result, f"t('vi', '{key}') returned empty"
        assert _vi_tbd(result) is False


# ── Structural sanity ───────────────────────────────────────────────────────


class TestStructural:
    def test_messages_has_en_and_vi(self) -> None:
        assert "en" in MESSAGES
        assert "vi" in MESSAGES

    def test_messages_en_points_to_prompt_en(self) -> None:
        assert MESSAGES["en"] is PROMPT_EN

    def test_messages_vi_points_to_prompt_vi(self) -> None:
        assert MESSAGES["vi"] is PROMPT_VI

    def test_default_locale_is_en(self) -> None:
        assert DEFAULT_LOCALE == "en"

    def test_get_messages_en(self) -> None:
        bundle = get_messages("en")
        assert bundle is PROMPT_EN

    def test_get_messages_vi(self) -> None:
        bundle = get_messages("vi")
        assert bundle is PROMPT_VI

    def test_get_messages_unknown_falls_back_to_en(self) -> None:
        bundle = get_messages("zz")
        assert bundle is PROMPT_EN

    def test_prompt_en_minimum_entries(self) -> None:
        assert len(PROMPT_EN) >= 20, "PROMPT_EN has suspiciously few entries"

    def test_prompt_vi_minimum_entries(self) -> None:
        assert len(PROMPT_VI) >= 20, "PROMPT_VI has suspiciously few entries"
