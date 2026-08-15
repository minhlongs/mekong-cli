# API Versioning

Versioning strategy for Mekong CLI APIs.

---

## Versioning Policy

Mekong APIs are versioned using **URL path versioning**: `/api/v1/`, `/api/v2/`, etc.

**Key principles:**

- **Breaking changes** → New major version (v1 → v2)
- **Backward-compatible changes** → Same version (add fields, new endpoints)
- **Deprecation period** → Old versions supported for 12 months after new version release
- **Version identifier** → Integer major version (no `v1.2.3`, just `v1`)

---

## What Constitutes a Breaking Change?

| Breaking Change | New Version Required? |
|-----------------|-----------------------|
| Remove endpoint | ✅ Yes |
| Change endpoint URL | ✅ Yes |
| Remove required request field | ✅ Yes |
| Change field type (string → int) | ✅ Yes |
| Rename field | ✅ Yes |
| Change authentication mechanism | ✅ Yes |
| Add new optional field | ❌ No |
| Add new endpoint | ❌ No |
| Add new response field | ❌ No |
| Change error format (add fields) | ❌ No |

---

## Version Lifecycle

```
Release v1.0.0 ──────────────────────────────────────┐
                                                        │
Announce v2.0.0 (deprecation notice) ────────────────┤ 12 months
                                                        │
v1 sunset (return 410 Gone) ──────────────────────────┘
```

**Timeline:**

1. **vN released** — Current stable version
2. **vN+1 announced** — Blog post, email, dashboard notice. vN marked "Deprecated".
3. **12-month deprecation period** — Both versions supported. Clients should migrate.
4. **vN sunset** — vN endpoints return `410 Gone`. Requests redirected to migration guide.
5. **vN+1 becomes stable** — Only vN+1 receives new features.

---

## Current Versions

| API | Current Version | Deprecated Versions | Sunset Date |
|-----|-----------------|---------------------|-------------|
| Core Gateway (`mekongd`) | v1 | None | N/A |
| Agent Forest | v1 | None | N/A |
| Partner | v1 | None | N/A |

---

## Deprecation Notices

When an endpoint is deprecated:

1. **Documentation:** Marked with `deprecated: true` in OpenAPI spec
2. **Response Headers:** `Sunset: Tue, 31 Dec 2027 23:59:59 GMT`
3. **Link to migration:** `Link: <https://docs.mekong.cli/migration/v1-to-v2>; rel="migration"`
4. **Warning Header:** `Warning: 299 - "This API version is deprecated"`

**Example response:**

```http
HTTP/1.1 200 OK
Sunset: Tue, 31 Dec 2027 23:59:59 GMT
Link: <https://docs.mekong.cli/migration/v1-to-v2>; rel="migration"
Warning: 299 - "API version v1 is deprecated. Migrate to v2 before 2027-12-31"
```

---

## Migrating Between Versions

When a new major version is released:

1. **Read migration guide:** [docs.mekong.cli/migration/v1-to-v2](https://docs.mekong.cli/migration/v1-to-v2)
2. **Update base URL:** Change `/api/v1/` → `/api/v2/`
3. **Update request payloads:** New required fields, renamed fields
4. **Update response handling:** Changed status codes, new error codes
5. **Test in staging:** `https://staging-api.mekong.cli/api/v2/`
6. **Deploy changes** before sunset date

---

## Example: v1 → v2 Changes

### v1

```json
POST /api/v1/commands/execute
{
  "command": "/test/echo",
  "args": {"message": "hello"}
}
```

### v2

```json
POST /api/v2/commands/execute
{
  "command": "/test/echo",
  "arguments": {"message": "hello"},
  "async": false  # New optional field
}
```

**Changes:**

- `args` renamed to `arguments`
- Added `async` option (backward-compatible addition, but requires client update if they send `args`)

---

## Version Negotiation

If client requests an unsupported version:

```http
GET /api/v3/commands
```

Response:

```http
HTTP/1.1 400 Bad Request
X-Supported-Versions: v1, v2
X-Current-Version: v2
```

```json
{
  "detail": "API version v3 not supported. Supported: v1, v2. Current: v2",
  "code": "API_VERSION_UNSUPPORTED"
}
```

---

## Backward Compatibility Guarantees

**We guarantee:**

- v1 endpoints remain functional for 12 months after v2 release
- No silent breaking changes within a major version
- Clear deprecation warnings before sunset
- Migration guides for all breaking changes

**We do NOT guarantee:**

- Bug fixes for deprecated versions (only security fixes)
- New features in old versions
- Support for versions older than current -1 (e.g., if v3 is current, v1 gets no support)

---

## Semantic Versioning in URLs

Why not use `/api/1.2.3`?

- **URL versioning uses major version only** (simpler)
- Minor/patch versions track implementation, not API contract
- If you need backward compatibility within major version, you must maintain it
- Clients should not depend on minor version differences

---

## Staging Environment

Test new API versions before production:

```
https://staging-api.mekong.cli/api/v2/
https://api.mekong.cli/api/v2/  # Production
```

Staging mirrors production but with test data.

---

## Changelog

Track API changes in `CHANGELOG.md`:

```markdown
## [2.0.0] - 2026-12-01

### Changed
- `/api/v1/commands/execute` → `/api/v2/commands/execute`
- Renamed `args` to `arguments` in request body
- Added `async` parameter for background execution

### Deprecated
- `/api/v1/*` endpoints (sunset: 2027-12-01)
```

---

## Best Practices for Clients

1. **Pin to major version** in production (`/api/v1/`, not `/api/latest/`)
2. **Monitor deprecation notices** — Subscribe to API status emails
3. **Test new versions** in staging 3-6 months before sunset
4. **Use feature flags** to support multiple versions during migration
5. **Graceful degradation** — If v2 unavailable, fallback to v1 during transition

---

## FAQ

**Q: What if I don't migrate before sunset?**  
A: v1 endpoints return `410 Gone`. You must migrate to v2.

**Q: Can you extend the deprecation period?**  
A: In exceptional cases, contact support. We rarely extend beyond 12 months.

**Q: Will minor updates break my integration?**  
A: No. Minor/patch versions maintain backward compatibility.

**Q: How do I know which version I'm using?**  
A: Check the URL path (`/api/v1/`) or call `GET /api/version`.

**Q: Is there an SDK?**  
A: Yes! SDKs handle versioning automatically. Upgrade SDK to get new API version.

---

## See Also

- [API Reference](../reference/API_REFERENCE.md)
- [Changelog](../../CHANGELOG.md)
- [Migration Guides](https://docs.mekong.cli/migration/)

---

**Current Stable Version:** v1  
**Latest Development Version:** v2 (in beta)  
**Versioning Scheme:** Major version in URL, semantic versioning for releases
