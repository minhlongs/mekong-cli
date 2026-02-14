# XSS Vectors Security Audit -- sophia-ai-factory

**Date:** 2026-02-11
**Auditor:** code-reviewer (subagent)
**Scope:** All `.tsx`, `.ts` files under `apps/sophia-ai-factory/apps/sophia-ai-factory/src/`
**LOC Scanned:** ~120 source files (excluding node_modules, tests)

---

## Overall Assessment

**Risk Level: LOW-MEDIUM**

Codebase co thiet ke bao mat tot. Khong co `dangerouslySetInnerHTML` nao. React tu dong escape text content trong JSX. CSP headers duoc cau hinh day du. Tuy nhien, co mot so vector can xu ly de tang cuong bao mat phong thu sau (defense-in-depth).

---

## Findings

### FINDING 1: YouTube Embed -- iframe src khong validate videoId

**Severity:** MEDIUM
**File:** `/src/components/guide/youtube-embed.tsx` (line 5)
**Code:**
```tsx
src={`https://www.youtube.com/embed/${videoId}`}
```

**Attack Vector:** Neu `videoId` nhan gia tri user-controlled, attacker co the inject query parameters hoac path traversal vao YouTube embed URL. Vi du: `videoId = "abc?autoplay=1&loop=1"` hoac tham chi `videoId = '"><script>'` (duoc CSP chan nhung van la bad practice).

**Mitigating Factors:**
- CSP `frame-src 'self' https://www.youtube.com` gioi han iframe chi load tu YouTube
- Hien tai chi dung voi hardcoded IDs trong guide pages
- YouTube embed URL tu escape XSS trong path

**Fix:**
```tsx
// Validate videoId format (YouTube IDs are 11 alphanumeric chars)
const YOUTUBE_ID_REGEX = /^[a-zA-Z0-9_-]{11}$/;
export function YouTubeEmbed({ videoId, title }: { videoId: string; title: string }) {
  if (!YOUTUBE_ID_REGEX.test(videoId)) return null;
  // ...
}
```

---

### FINDING 2: Dynamic URLs trong href/src khong co protocol validation

**Severity:** MEDIUM
**Files:**
- `/src/components/video-preview.tsx` (lines 95, 137)
- `/src/app/[locale]/dashboard/components/project-card.tsx` (line 81)
- `/src/app/[locale]/dashboard/components/campaign-list/campaign-actions.tsx` (line 71)

**Code patterns:**
```tsx
// video-preview.tsx:137
<a href={videoUrl} download target="_blank" rel="noopener noreferrer">

// project-card.tsx:81
<a href={project.videoUrl} target="_blank" rel="noopener noreferrer">

// campaign-actions.tsx:71
<a href={campaign.video_url} target="_blank" rel="noopener noreferrer">
```

**Attack Vector:** Neu `video_url` hoac `videoUrl` trong database chua `javascript:alert(1)`, click vao link se execute JavaScript. Du `target="_blank"` va `rel="noopener"` co mat, chung khong ngan `javascript:` protocol execution.

**Data Flow:**
1. Campaign duoc tao qua form -> server action -> database
2. `video_url` duoc set boi HeyGen API response (trusted)
3. NHUNG: Neu database bi compromise hoac API response bi tamper, vector nay mo

**Mitigating Factors:**
- Zod schema validate `video_url` voi `.url()` (chi accept valid URLs) -- dong 15 `schemas.ts`
- CSP `default-src 'self'` gioi han script execution
- Data den tu trusted HeyGen API, khong truc tiep tu user input

**Fix:**
```tsx
function isSafeHref(url: string | null | undefined): string | undefined {
  if (!url) return undefined;
  try {
    const parsed = new URL(url);
    if (['http:', 'https:'].includes(parsed.protocol)) return url;
  } catch {}
  return undefined;
}

// Usage:
<a href={isSafeHref(videoUrl)} ...>
```

---

### FINDING 3: CSP co `unsafe-inline` cho script-src

**Severity:** MEDIUM
**File:** `/next.config.ts` (line 65)
**CSP:**
```
script-src 'self' 'unsafe-inline'
```

**Attack Vector:** `unsafe-inline` cho phep inline scripts execute. Neu co bat ky injection point nao (du nho), attacker co the inject inline `<script>` tag. Tuy nhien, vi khong co `dangerouslySetInnerHTML`, vector nay hien tai chi la ly thuyet.

**Mitigating Factors:**
- Next.js can `unsafe-inline` de hoat dong (inline scripts cho hydration)
- Khong co `dangerouslySetInnerHTML` trong codebase
- React tu dong escape JSX output

**Fix:**
```
// Su dung nonce-based CSP (Next.js 13+ ho tro)
// next.config.ts:
experimental: { serverActions: true },
// Dung middleware de generate nonce per request
```

**Note:** Day la van de kien truc can can nhac ky, khong phai quick fix.

---

### FINDING 4: CSP thieu `object-src 'none'`

**Severity:** LOW
**File:** `/next.config.ts` (line 65)

**Attack Vector:** Thieu `object-src` directive cho phep `<object>`, `<embed>`, `<applet>` tags load tu bat ky nguon nao. Tuy nhien, vi khong co injection point de chen cac tag nay (no `dangerouslySetInnerHTML`), risk la thap.

**Fix:** Them `object-src 'none';` vao CSP string.

---

### FINDING 5: ReactMarkdown trong GuideContentRenderer

**Severity:** LOW
**File:** `/src/components/guide/guide-content-renderer.tsx` (line 27)
**Code:**
```tsx
<ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
```

**Attack Vector:** `content` prop la string duoc render thanh Markdown. ReactMarkdown **mac dinh KHONG render raw HTML** (can `rehype-raw` plugin). Noi dung den tu cac guide pages (static/hardcoded).

**Mitigating Factors:**
- Khong dung `rehype-raw` plugin -- HTML bi escape
- `content` den tu static guide data, khong phai user input
- Link nang cao: ReactMarkdown co sanitize URLs trong `[text](url)` format

**Recommendation:** Giu nguyen, nhung NEU tuong lai dung `rehype-raw`, BAT BUOC them `rehype-sanitize`.

---

### FINDING 6: `window.location.href = data.url` -- Open Redirect risk

**Severity:** LOW
**File:** `/src/components/pricing-section.tsx` (line 187)
**Code:**
```tsx
const data = await response.json();
if (data.url) {
  window.location.href = data.url;
}
```

**Attack Vector:** Neu `/api/checkout` response bi tamper (man-in-the-middle, hoac server-side bug), `data.url` co the la `javascript:alert(1)` hoac phishing URL.

**Mitigating Factors:**
- `/api/checkout` POST route dung Zod validation (`checkoutSchema`)
- URL den tu Polar SDK (`paymentService.createCheckoutSession`), la trusted source
- `javascript:` protocol trong `window.location.href` **KHONG** execute JavaScript (chi trong href attribute cua anchor tag)
- HTTPS + HSTS dam bao khong co MITM

**Actual risk: MINIMAL** -- `window.location.href = "javascript:..."` redirect toi URL literal, khong execute code.

---

### FINDING 7: CSV Export -- Sai escaping logic (CSV Injection)

**Severity:** MEDIUM (CSV Injection, khong phai XSS truc tiep)
**File:** `/src/lib/export-utils.ts` (lines 11-12)
**Code:**
```ts
const escaped = ("" + (row[header] ?? "")).replace(/"/g, '\\"');
return `"${escaped}"`;
```

**Attack Vector:** CSV escaping dung backslash (`\"`) thay vi RFC 4180 standard (`""`). Ngoai ra, khong co bao ve chong CSV injection -- neu cell bat dau bang `=`, `+`, `-`, `@`, `\t`, `\r`, attacker co the inject formula: `=CMD('calc')`.

**Fix:**
```ts
const escaped = ("" + (row[header] ?? ""))
  .replace(/"/g, '""')  // RFC 4180: double quotes
  // CSV injection prevention:
  .replace(/^([=+\-@\t\r])/, "'$1");  // Prefix with single quote
return `"${escaped}"`;
```

---

### FINDING 8: Error messages reflected trong UI

**Severity:** LOW (Khong XSS, nhung co the UI deception)
**Files:**
- `/src/components/video-preview.tsx` (line 45): `{errorMessage || "..."}`
- `/src/app/[locale]/login/page.tsx` (line 117): `{errorMsg}`
- `/src/app/[locale]/dashboard/components/create-campaign/campaign-form.tsx` (line 164): `{error}`

**Analysis:** Tat ca deu render error messages nhu text content trong JSX. React tu dong escape HTML entities, nen KHONG co XSS risk. Tuy nhien, error messages co the chua noi dung confusing hoac misleading neu den tu untrusted API responses.

**Mitigating Factors:** React auto-escaping dam bao an toan.

---

### FINDING 9: Khong co sanitization library (defense-in-depth gap)

**Severity:** LOW (hien tai), MEDIUM (tuong lai)
**Observation:** Khong co `DOMPurify`, `sanitize-html`, `rehype-sanitize` hoac bat ky sanitization library nao duoc install.

**Current Risk:** Thap, vi khong co `dangerouslySetInnerHTML` va React tu dong escape.

**Future Risk:** Neu developer them `dangerouslySetInnerHTML` hoac `rehype-raw` ma khong nho install sanitizer, se tao XSS vector ngay lap tuc.

**Recommendation:** Install `dompurify` hoac `isomorphic-dompurify` nhu dependency phong ve. Them eslint rule cam `dangerouslySetInnerHTML` ma khong co sanitization.

---

### FINDING 10: Image src tu database

**Severity:** LOW
**Files:**
- `/src/components/video-preview.tsx` (line 107): `src={thumbnailUrl}`
- `/src/components/discovery/product-card.tsx` (line 24): `src={product.thumbnail_url}`

**Mitigating Factors:**
- Next.js `<Image>` component validate domains qua `remotePatterns` trong `next.config.ts`
- Chi allow `v5.airtableusercontent.com` va `*.public.blob.vercel-storage.com`
- Invalid domains se bi Next.js reject voi runtime error

---

## Positive Observations

1. **Zero `dangerouslySetInnerHTML`** -- Toan bo codebase khong co mot instance nao. Day la practice tot nhat.

2. **CSP headers day du** -- `Content-Security-Policy`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Strict-Transport-Security` deu duoc cau hinh.

3. **Zod validation tren tat ca API routes** -- `campaignSchema`, `checkoutSchema`, `createVideoSchema` deu validate input voi Zod truoc khi xu ly.

4. **SSRF protection** -- `/api/discovery/validate-link/route.ts` co `isSafeUrl()` function chan internal IPs, non-HTTPS, metadata endpoints.

5. **`rel="noopener noreferrer"`** -- Tat ca external links deu co attribute nay, ngan tab-napping attack.

6. **Webhook authentication** -- Telegram webhook verify `X-Telegram-Bot-Api-Secret-Token`. API routes verify `CRON_SECRET` hoac Supabase auth.

7. **Search API filters sensitive data** -- `/api/discovery/search` remove `affiliate_link` va `raw_metrics` tu response.

8. **react-hook-form + zodResolver** -- Settings form dung validation pipeline chuan.

9. **Next.js Image domain restriction** -- `remotePatterns` gioi han image sources.

---

## Summary Table

| # | Finding | Severity | File | Status |
|---|---------|----------|------|--------|
| 1 | YouTube videoId khong validate | MEDIUM | `youtube-embed.tsx:5` | Open |
| 2 | Dynamic URLs khong check protocol | MEDIUM | `video-preview.tsx:137`, `project-card.tsx:81`, `campaign-actions.tsx:71` | Partial (Zod validates on input) |
| 3 | CSP `unsafe-inline` cho scripts | MEDIUM | `next.config.ts:65` | Open (architectural) |
| 4 | CSP thieu `object-src 'none'` | LOW | `next.config.ts:65` | Open |
| 5 | ReactMarkdown render content | LOW | `guide-content-renderer.tsx:27` | Safe (no rehype-raw) |
| 6 | `window.location.href = data.url` | LOW | `pricing-section.tsx:187` | Safe (trusted API source) |
| 7 | CSV injection in export | MEDIUM | `export-utils.ts:11-12` | Open |
| 8 | Error messages reflected | LOW | Multiple files | Safe (React auto-escape) |
| 9 | No sanitization library | LOW | N/A | Recommendation |
| 10 | Image src tu database | LOW | Multiple files | Safe (Next.js domain check) |

---

## Recommended Actions (Priority Order)

1. **[HIGH]** Fix CSV export escaping (`export-utils.ts`) -- RFC 4180 + CSV injection prevention
2. **[HIGH]** Add protocol validation helper for dynamic `<a href>` attributes
3. **[MEDIUM]** Validate YouTube videoId format with regex
4. **[MEDIUM]** Add `object-src 'none'` vao CSP
5. **[LOW]** Install `dompurify` nhu dependency phong ve
6. **[LOW]** Add ESLint rule `react/no-danger` de cam `dangerouslySetInnerHTML`
7. **[FUTURE]** Migrate tu `unsafe-inline` sang nonce-based CSP khi Next.js ho tro tot hon

---

## Unresolved Questions

1. Data source cua `guide-content-renderer.tsx` -- content den tu dau? Static files hay CMS? Neu CMS, can them `rehype-sanitize`.
2. Co plan nao render user-generated HTML content trong tuong lai khong? Neu co, BAT BUOC install sanitizer truoc.
3. `affiliate-programs.json` -- file nay duoc update tu dong hay manual? Neu tu dong (crawler), can validate `link` field.
