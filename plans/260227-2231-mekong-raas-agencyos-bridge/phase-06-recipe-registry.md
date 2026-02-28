# Phase 06: Recipe Registry

## Context Links
- [Existing recipe_gen](../../src/core/recipe_gen.py) — RecipeGenerator
- [Gateway recipe endpoints](../../src/core/gateway.py) — /recipes/generate, /recipes/auto
- [Research: RaaS outcomes](research/researcher-01-open-core-raas-models.md) — Section 3

## Overview
- **Priority:** P3
- **Status:** pending
- **Group:** B (after Group A; parallel with Phase 04, 05)
- **Est:** 2h

Public recipe marketplace. Community shares pre-built automation recipes. Tenants browse/clone recipes for their missions.

## Key Insights
- RecipeGenerator already creates/validates recipes
- Gateway has `/recipes/auto`, `/recipes/generate`, `/recipes/validate`
- Registry adds: tenant-published recipes, categories, search, popularity ranking
- VN market recipes: menu update, social post, inventory report, customer reply

## Requirements

### Functional
- `GET /raas/recipes` — browse public recipes (search, category filter)
- `GET /raas/recipes/{id}` — get recipe detail
- `POST /raas/recipes` — publish recipe (tenant auth required)
- `POST /raas/recipes/{id}/clone` — clone recipe to tenant's collection
- Categories: `marketing`, `operations`, `content`, `analytics`, `custom`

### Non-Functional
- Search by keyword in recipe name + description
- Pagination: limit/offset
- Recipe content validated before publish

## File Ownership (EXCLUSIVE)

| Action | File |
|--------|------|
| CREATE | `src/raas/registry.py` |

## Implementation Steps

1. Create `src/raas/registry.py`:
   - `RecipeEntry` dataclass: id, name, description, category, content, author_tenant_id, is_public, clone_count, created_at
   - `RecipeRegistry` class (SQLite):
     - `publish(tenant_id, name, description, category, content) -> RecipeEntry`
     - `search(query, category, limit, offset) -> List[RecipeEntry]`
     - `get(recipe_id) -> Optional[RecipeEntry]`
     - `clone(recipe_id, tenant_id) -> RecipeEntry` — copies to tenant's private collection
   - Validate content via existing `RecipeGenerator.validate_recipe()`
   - FastAPI router: `raas_registry_router`
   - Mount: `gateway.include_router(raas_registry_router, prefix="/raas")`

## Todo List
- [ ] Create RecipeEntry model and SQLite table
- [ ] Implement RecipeRegistry with search + publish + clone
- [ ] Create FastAPI router (4 endpoints)
- [ ] Seed with 5 starter recipes (VN SMB templates)
- [ ] Unit tests: `tests/test_raas_registry.py`

## Success Criteria
- Publish recipe, search by keyword, clone to tenant
- Category filter works
- Content validation rejects invalid recipes
- Tests pass: `pytest tests/test_raas_registry.py`

## Risk Assessment
- **Spam recipes:** v1 = only authenticated tenants publish. Moderation in v2.
- **Recipe quality:** Validated via RecipeGenerator; invalid recipes rejected.
