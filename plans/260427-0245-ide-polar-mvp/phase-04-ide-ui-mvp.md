# Phase 04: IDE UI MVP — CLI-in-Browser

**Priority:** P0 — User-facing
**Status:** ✅ SCAFFOLDED (ready for implementation)
**Effort:** 5-7 ngày
**Last Verified:** 2026-04-27 — specs defined, components structure ready
**Depends on:** Phase 03 (license gating + auth endpoints)

## Context Links

- `apps/ide-ui/` — Next.js 14 app, currently chỉ landing page
- `apps/ide-ui/app/{layout.tsx, page.tsx, departments/}` — current pages
- `apps/ide-ui/wrangler.toml` — Cloudflare Pages config (frontend only)
- `apps/ide-ui/package.json:scripts` — `dev`, `build`

## Overview

Hiện tại `ide.mekongmind.com` là landing tĩnh. Phase này thêm **CLI-in-browser** cho user paid:
- Login với license key
- Terminal-style interface (xterm.js)
- Submit mission, xem stream output realtime
- Hiển thị MCU balance + recharge link

**KHÔNG làm:** Monaco editor, file browser, multi-tab, marketplace UI. Defer hết.

## Architecture

```
ide.mekongmind.com
├── /                    Landing (existing)
├── /login               License key input
├── /app                 Authenticated CLI-in-browser
│   ├── xterm.js terminal
│   ├── header: balance MCU, recharge button
│   └── footer: connection status
└── /pricing             redirect → www.mekongmind.com/pricing
```

Auth flow:
```
1. User → /login → POST api.mekong.dev/auth/login {license_key}
2. Receive {access_token, refresh_token}
3. Store in httpOnly cookie (or localStorage with caveat)
4. Redirect → /app
5. /app: connect SSE to api.mekong.dev/v1/missions/stream với Bearer token
```

Mission flow:
```
1. User gõ "scout user model" + Enter
2. Frontend POST api.mekong.dev/v1/missions {goal: "scout user model"}
3. Receive {mission_id, stream_url}
4. EventSource(stream_url + "?token=<jwt>") → live output
5. On complete: refetch balance, update header
```

## Requirements

### Functional
- `/login` page — license key input, error states (invalid/expired/inactive)
- `/app` page — gated by JWT cookie/localStorage; redirect /login nếu missing
- xterm.js terminal — readonly output area + input line
- Header — current MCU balance (poll every 30s), recharge button
- Connection status indicator (green/yellow/red)
- Mobile responsive — work on iPad portrait min

### Non-Functional
- Page load < 2s on 3G (Cloudflare Pages edge cache)
- xterm.js bundle < 200KB gzipped
- SSE reconnect on disconnect (max 3 retries, exponential backoff)

## Related Code Files

### Modify
- `apps/ide-ui/app/layout.tsx` — add auth provider (React Context)
- `apps/ide-ui/package.json` — add deps: `xterm`, `xterm-addon-fit`, `xterm-addon-web-links`, `@tanstack/react-query`

### Create
- `apps/ide-ui/app/login/page.tsx` — license key form
- `apps/ide-ui/app/app/page.tsx` — main CLI page
- `apps/ide-ui/app/app/layout.tsx` — auth guard wrapper
- `apps/ide-ui/components/terminal.tsx` — xterm.js wrapper
- `apps/ide-ui/components/balance-header.tsx` — MCU balance + recharge button
- `apps/ide-ui/lib/api-client.ts` — fetch wrapper with auth header injection
- `apps/ide-ui/lib/sse-client.ts` — SSE consumer with reconnect
- `apps/ide-ui/lib/auth.ts` — JWT storage + refresh logic
- `apps/ide-ui/middleware.ts` — Next.js middleware for `/app/*` auth redirect

### Delete
- None

## Implementation Steps

1. **Install deps**
   ```bash
   cd apps/ide-ui
   pnpm add xterm xterm-addon-fit xterm-addon-web-links @tanstack/react-query
   ```

2. **Auth library** — `lib/auth.ts`:
   ```typescript
   export async function login(licenseKey: string): Promise<{accessToken: string}>
   export function getToken(): string | null
   export function logout(): void
   export async function refresh(): Promise<string>
   ```

3. **API client** — `lib/api-client.ts`:
   - Wrap fetch, inject `Authorization: Bearer <token>`
   - On 401 → call `refresh()`, retry once
   - On 402 → throw `InsufficientCreditsError` with `recharge_url`

4. **SSE client** — `lib/sse-client.ts`:
   - EventSource with token in URL query (browser EventSource doesn't support headers)
   - On error → exponential backoff reconnect (1s, 2s, 4s, give up after 3)

5. **Terminal component** — `components/terminal.tsx`:
   - xterm.js init with FitAddon
   - `onInput` callback when user presses Enter
   - `write(text)` method to stream output
   - Theme: dark background, monospace, green prompt

6. **Balance header** — `components/balance-header.tsx`:
   - useQuery({queryKey: ['balance'], refetchInterval: 30000})
   - Show "MCU: 142 / 1000" + recharge button (link to www.mekongmind.com/billing)

7. **App page** — `app/app/page.tsx`:
   - Mount `<Terminal>` + `<BalanceHeader>`
   - On user input: POST `/v1/missions`, open SSE, pipe to terminal

8. **Login page** — `app/login/page.tsx`:
   - Form, on submit: call `login()`, redirect `/app`
   - Error messages cho 401 (invalid) / 402 (inactive license)

9. **Auth guard middleware** — `middleware.ts`:
   - If `/app/*` and no token cookie → redirect `/login`

10. **Build + deploy** — `pnpm build && wrangler pages deploy out/`

## Todo List

- [ ] `pnpm add xterm` etc.
- [ ] `lib/auth.ts` (~80 lines)
- [ ] `lib/api-client.ts` (~70 lines)
- [ ] `lib/sse-client.ts` (~90 lines)
- [ ] `components/terminal.tsx` (~120 lines)
- [ ] `components/balance-header.tsx` (~60 lines)
- [ ] `app/login/page.tsx` (~80 lines)
- [ ] `app/app/page.tsx` (~100 lines)
- [ ] `app/app/layout.tsx` (~30 lines)
- [ ] `middleware.ts` (~30 lines)
- [ ] Vitest tests for `lib/auth.ts`, `lib/api-client.ts`
- [ ] Playwright smoke test: login → submit → output
- [ ] Build green: `pnpm build` exit 0
- [ ] Bundle analyze — terminal page < 300KB gzipped
- [ ] Deploy: `wrangler pages deploy out --project-name=ide-ui`
- [ ] Verify `https://ide.mekongmind.com/app` HTTP 200 (redirect /login OK)

## Success Criteria

- User mở `ide.mekongmind.com/login`, paste license key → redirect `/app`
- Terminal hiển thị, gõ command + Enter → output stream
- MCU balance hiển thị đúng, giảm sau mỗi mission
- Reload page giữ login (token persist)
- Logout clears token, back to `/login`
- Mobile (375px width) UI usable

## Risk Assessment

| Risk | Mitigation |
|---|---|
| EventSource không support header → token trong URL query bị log | Use POST + manual SSE polyfill nếu cần; ngắn-lived JWT (5 min) |
| xterm.js bundle quá to | Code split, dynamic import; lazy load on /app only |
| CORS preflight với SSE | Phase 01 set CORS đúng; SSE đơn giản hoá với GET |
| Token leak qua localStorage XSS | CSP strict; sanitize all user-controlled output xuất ra terminal |

## Security Considerations

- CSP header: `default-src 'self'; connect-src api.mekong.dev`
- HttpOnly cookie cho refresh token (XSS không lấy được)
- Access token có thể localStorage (1h TTL chấp nhận được)
- xterm.js render output: escape ANSI sequences malicious
- Rate limit POST `/v1/missions` từ frontend (debounce 1s)

## Next Steps

Phase 05 — E2E Playwright test toàn bộ flow này.
