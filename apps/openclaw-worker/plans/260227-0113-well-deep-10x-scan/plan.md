# Deep 10x Scan — Well Project (Binh Pháp 100/100)

> 始計 — Tính toán ban đầu trước khi chiến

## Tổng Quan

**Project:** WellNexus Distributor Portal
**Stack:** React + TypeScript + Vite + Zustand + Framer Motion
**Path:** `/Users/macbookprom1/mekong-cli/apps/well`
**Mục tiêu:** Triệt tiêu tech debt, inject ClaudeKit DNA + Binh Pháp mapping

## Kết Quả Scan (5 Research Agents)

| Hạng Mục | Số Lượng | Severity |
|-----------|----------|----------|
| Silent catch blocks | 54 | 🔴 CRITICAL |
| EN [MISSING] translations | 1,244 | 🔴 CRITICAL |
| Missing loading states | 6 hooks | 🔴 HIGH |
| Missing error states | 5 hooks/stores | 🔴 HIGH |
| Hardcoded strings (non-i18n) | ~10 | 🟡 MEDIUM |
| `as any` usage | 3 (tests only) | 🟡 LOW |
| `console.warn` in prod | 1 | 🟡 LOW |
| usePolicyEngine over-state | 11 useState | 🟡 MEDIUM |
| TODO/FIXME | 0 | ✅ CLEAN |
| Circular deps | 0 | ✅ CLEAN |

## Quy Tắc: TỐI ĐA 5 FILE MỖI MISSION

Chia thành 6 mission, mỗi mission ≤ 5 file.

---

## Phase 1: Silent Catch → Logger (5 files) — 🔴 P0
**Status:** ⬜ Pending

Fix 4 security-critical utils + 1 network util. Thêm error logging qua logger.ts.

**Files:**
1. `src/utils/secure-token-storage.ts` (4 silent catches)
2. `src/utils/clipboard.ts` (3 silent catches)
3. `src/utils/security.ts` (4 silent catches)
4. `src/utils/notifications.ts` (2 silent catches)
5. `src/utils/network.ts` (1 silent catch)

**Action:** Replace `catch {}` → `catch (error) { logger.error('context', { error }); }`

→ [phase-01-silent-catch-security-utils.md](phase-01-silent-catch-security-utils.md)

---

## Phase 2: Silent Catch → Logger (5 files) — 🔴 P0
**Status:** ⬜ Pending

Fix remaining utility files with silent catches.

**Files:**
1. `src/utils/storage.ts` (2 silent catches)
2. `src/utils/url.ts` (2 silent catches)
3. `src/utils/random.ts` (1 silent catch)
4. `src/utils/encoding.ts` (1 silent catch)
5. `src/utils/eventBus.ts` (multiple)

→ [phase-02-silent-catch-general-utils.md](phase-02-silent-catch-general-utils.md)

---

## Phase 3: Silent Catch Remaining + Loading States (5 files) — 🔴 P0
**Status:** ⬜ Pending

Fix async/performance utils + add loading states to critical hooks.

**Files:**
1. `src/utils/async.ts` (multiple silent catches)
2. `src/utils/performance.ts` (1 silent catch)
3. `src/utils/safari-crypto-polyfills.ts` (multiple)
4. `src/hooks/useAuth.ts` (missing loading state)
5. `src/store/index.ts` (missing error exposure)

→ [phase-03-catch-and-loading-states.md](phase-03-catch-and-loading-states.md)

---

## Phase 4: Hook Error Handling + State Simplification (5 files) — 🟠 P1
**Status:** ⬜ Pending

Fix error boundaries in async hooks, simplify usePolicyEngine.

**Files:**
1. `src/hooks/useDashboard.ts` (missing try-catch on map)
2. `src/hooks/usePolicyEngine.ts` (11 useState → consolidated)
3. `src/store/slices/authSlice.ts` (missing loading/error states)
4. `src/store/slices/walletSlice.ts` (circular state updates)
5. `src/hooks/useForm.ts` (error not propagated)

→ [phase-04-hook-error-handling.md](phase-04-hook-error-handling.md)

---

## Phase 5: i18n EN [MISSING] — Top 5 Modules (5 files) — 🔴 P0
**Status:** ⬜ Pending

Translate 5 highest-impact EN modules (599 [MISSING] keys total).

**Files:**
1. `src/locales/en/team.ts` (171 missing)
2. `src/locales/en/marketplace.ts` (163 missing)
3. `src/locales/en/wallet.ts` (148 missing)
4. `src/locales/en/admin.ts` (117 missing)
5. `src/locales/en/marketing.ts` (132 missing — BONUS if time)

→ [phase-05-i18n-en-top-modules.md](phase-05-i18n-en-top-modules.md)

---

## Phase 6: i18n Remaining + Hardcoded Strings (5 files) — 🟠 P1
**Status:** ⬜ Pending

Fix remaining EN modules + hardcoded strings.

**Files:**
1. `src/locales/en/misc.ts` (121 missing)
2. `src/locales/en/health.ts` (93 missing)
3. `src/locales/en/dashboard.ts` (92 missing)
4. `src/locales/en/copilot.ts` (89 missing)
5. `src/components/OnboardingQuest.tsx` (hardcoded strings)

→ [phase-06-i18n-remaining-hardcoded.md](phase-06-i18n-remaining-hardcoded.md)

---

## Tech Debt Lan Rộng (Báo Cáo)

Các vấn đề KHÔNG fix trong scan này (cần mission riêng):

1. **40+ hooks thiếu loading state** — Cần audit hook-by-hook
2. **EN referral.ts** (64 missing), **auth.ts** (46 missing), **network.ts** (8 missing) — Phase 7
3. **26 [MISSING] keys trong VI** — Phase 8
4. **268 VI-only keys** không có EN — Cần product decision
5. **Namespace conflicts** (auth.signup vs auth.register) — Cần migration strategy
6. **Button.tsx console.warn** → logger.warn — Trivial, bundle vào commit

## Success Criteria

- [ ] 0 silent catch blocks trong security-critical utils
- [ ] Loading states trong useAuth + store/index.ts
- [ ] Error states exposed tới UI cho async operations
- [ ] Top 5 EN modules có actual translations (không còn [MISSING])
- [ ] Hardcoded strings trong OnboardingQuest → t()
- [ ] Build passes: `npm run build` exit 0
- [ ] Tests pass: `npx vitest run` exit 0
