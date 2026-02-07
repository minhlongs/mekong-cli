# Phase 04: i18n

> **Status**: Completed
> **Goal**: Implement internationalization using next-intl.

## Actions
1.  **Configuration**: Verified `src/i18n/request.ts` and `next.config.ts`.
2.  **Messages**: Audited `messages/` (en.json, vi.json) for completeness.
3.  **Components**: Ensured all text is wrapped in `useTranslations`.
4.  **Routing**: Verified `[locale]` routing works correctly.
5.  **Switcher**: Polished `LanguageSwitcher` component.

## Execution
- [x] Audit all TSX files for hardcoded strings.
- [x] Extract strings to JSON message files.
- [x] Implement `LocaleLayout` if missing.
- [x] Create `not-found.tsx` with translations.
- [x] Refactor `TerminalAnimation` and `CheckoutButton`.
- [x] Verify build success.

## Success Criteria
- [x] Switching language changes all text.
- [x] No unlocalized strings.
- [x] Correct URL structure (`/en`, `/vi`).
