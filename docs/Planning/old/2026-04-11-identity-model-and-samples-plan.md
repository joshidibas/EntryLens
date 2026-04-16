# Plan: Identity Model And Samples

## Task Summary

Define the next-stage data model and application plan around `Identity` as the canonical person record, with multiple stored face samples, profile-image support, and admin CRUD flows. This plan is intentionally centered on operator workflow and attendance-system structure first, with recognition quality treated as a later hardening phase.

## Current Repo Truth

Verified current implementation state:

- Backend currently uses `public.identities` and `public.embeddings` in [`entrylens-api/setup_supabase.sql`](/d:/Testproject2/VisitorsTrackers/entrylens-api/setup_supabase.sql).
- `identities` currently stores:
  - `id`
  - `name`
  - `role`
  - `provider_subject_id`
  - `created_at`
- `embeddings` currently stores:
  - `id`
  - `identity_id`
  - `embedding`
  - `metadata`
  - `created_at`
- Sample/reference behavior currently lives in `embeddings.metadata`, not first-class columns.
- Backend routes already exist for:
  - listing identities
  - listing samples per identity
  - adding a sample to an identity
  - deleting a sample
  - promoting a sample as preferred reference
- Frontend already has:
  - `/people`
  - `/people/:identityId`
  - table-based identity directory
  - table-based sample detail view
- Current recognition pipeline still uses MediaPipe transformation matrices as a placeholder matching vector. This is sufficient for UI and operator workflow scaffolding, but not reliable enough to define long-term identity semantics.

## What We Already Have

Current identity/sample surface in code:

- Identity directory API:
  [`entrylens-api/app/routes/identities.py`](/d:/Testproject2/VisitorsTrackers/entrylens-api/app/routes/identities.py)
- Supabase helpers:
  [`entrylens-api/app/supabase.py`](/d:/Testproject2/VisitorsTrackers/entrylens-api/app/supabase.py)
- People UI:
  [`entrylens-frontend/src/pages/PeoplePage.tsx`](/d:/Testproject2/VisitorsTrackers/entrylens-frontend/src/pages/PeoplePage.tsx)
- Frontend identity API client:
  [`entrylens-frontend/src/api/identities.ts`](/d:/Testproject2/VisitorsTrackers/entrylens-frontend/src/api/identities.ts)

This means the next step is not a greenfield build. It is a data-model refinement and naming/domain upgrade from the current `people/identities + embeddings` shape into a stronger `Identity + IdentitySample` model.

## Assumptions

- We will keep the current physical tables and migrate them forward rather than replacing them immediately.
- `identities` can remain the base table name for now.
- `embeddings` should be evolved conceptually into `identity_samples`, but we should not rush a destructive rename until routes and data migration are stable.
- One stored sample can be chosen as the profile image source for an identity.
- Recognition quality is not yet the source of truth for identity correctness.
- Operator review and data management are the priority now.

## Proposed Domain Model

### 1. Identity

Canonical record for a person/entity in the system.

Recommended fields:

- `id uuid primary key`
- `display_name text not null`
- `identity_type text not null default 'visitor'`
- `status text not null default 'active'`
- `notes text null`
- `profile_sample_id uuid null`
- `provider_subject_id text null`
- `created_at timestamptz not null default now()`
- `updated_at timestamptz not null default now()`

Mapping from current schema:

- current `name` -> future `display_name`
- current `role` -> future `identity_type`
- current `provider_subject_id` stays

### 2. IdentitySample

Stored face sample tied to one identity. This is the operator-visible unit for review, deletion, reference-promotion, and later image/profile selection.

Recommended fields:

- `id uuid primary key`
- `identity_id uuid not null references identities(id) on delete cascade`
- `sample_kind text not null default 'face'`
- `image_path text null`
- `embedding vector(16) null for now`
- `capture_source text null`
- `capture_confidence float null`
- `is_reference boolean not null default false`
- `is_profile_source boolean not null default false`
- `metadata jsonb null`
- `created_at timestamptz not null default now()`
- `updated_at timestamptz not null default now()`

Mapping from current schema:

- current table `embeddings` becomes this conceptually
- current `metadata.source` -> `capture_source`
- current `metadata.source_confidence` -> `capture_confidence`
- current `metadata.is_reference` -> `is_reference`

## Recommended Database Strategy

Do this in phases instead of renaming everything immediately.

### Phase A: Normalize The Existing Schema

Keep current table names:

- `identities`
- `embeddings`

Add columns to support the Identity domain cleanly:

#### `identities`

- add `display_name text`
- add `identity_type text`
- add `status text default 'active'`
- add `notes text`
- add `profile_sample_id uuid null`
- add `updated_at timestamptz default now()`

Backfill:

- `display_name = name`
- `identity_type = role`

Then later:

- frontend/backend reads `display_name` and `identity_type`
- old `name` and `role` can remain temporarily for compatibility

#### `embeddings`

Add:

- `sample_kind text default 'face'`
- `image_path text`
- `capture_source text`
- `capture_confidence float`
- `is_reference boolean default false`
- `is_profile_source boolean default false`
- `updated_at timestamptz default now()`

Backfill from `metadata` where possible:

- `capture_source = metadata->>'source'`
- `capture_confidence = (metadata->>'source_confidence')::float`
- `is_reference = coalesce((metadata->>'is_reference')::boolean, false)`

### Phase B: Optional Table Rename

Only after API and UI stabilize:

- rename `embeddings` -> `identity_samples`

This is not required for the next delivery milestone.

## Concrete SQL Draft

This is the recommended migration direction based on the schema we already have:

```sql
alter table public.identities
  add column if not exists display_name text,
  add column if not exists identity_type text,
  add column if not exists status text not null default 'active',
  add column if not exists notes text,
  add column if not exists profile_sample_id uuid,
  add column if not exists updated_at timestamptz not null default now();

update public.identities
set
  display_name = coalesce(display_name, name),
  identity_type = coalesce(identity_type, role);

alter table public.embeddings
  add column if not exists sample_kind text not null default 'face',
  add column if not exists image_path text,
  add column if not exists capture_source text,
  add column if not exists capture_confidence float,
  add column if not exists is_reference boolean not null default false,
  add column if not exists is_profile_source boolean not null default false,
  add column if not exists updated_at timestamptz not null default now();

update public.embeddings
set
  capture_source = coalesce(capture_source, metadata->>'source'),
  capture_confidence = coalesce(capture_confidence, nullif(metadata->>'source_confidence', '')::float),
  is_reference = coalesce(is_reference, false) or coalesce((metadata->>'is_reference')::boolean, false);
```

Note:

- `profile_sample_id` foreign-key enforcement should be added only after sample lifecycle is stable, because it introduces circular dependency between `identities` and `embeddings`.

## Recommended API Surface

### Identity routes

Keep `/api/v1/identities` as the public route family.

Add or evolve toward:

- `GET /api/v1/identities`
  - list identities for directory table
- `POST /api/v1/identities`
  - create new identity
- `GET /api/v1/identities/{id}`
  - identity detail
- `PATCH /api/v1/identities/{id}`
  - update display name, type, status, notes
- `DELETE /api/v1/identities/{id}`
  - archive/delete identity later

### Identity sample routes

- `GET /api/v1/identities/{id}/samples`
- `POST /api/v1/identities/{id}/samples`
- `GET /api/v1/identities/{id}/samples/{sampleId}`
- `DELETE /api/v1/identities/{id}/samples/{sampleId}`
- `POST /api/v1/identities/{id}/samples/{sampleId}/promote-reference`
- `POST /api/v1/identities/{id}/samples/{sampleId}/set-profile`

Current route compatibility:

- current `/embeddings`-backed routes can be kept and internally remapped while UI terminology moves to `samples`

## Recommended UI Surface

### 1. Identity Directory Page

Route:

- `/identities` or continue `/people` temporarily and later rename

Table columns:

- `Name`
- `Type`
- `Status`
- `Created / Added On`
- `Profile`
- `Samples`
- `Actions`

Actions:

- `View Samples`
- `Edit Identity`

### 2. Identity Detail Page

Route:

- `/identities/:identityId`

Sections:

- identity summary header
- profile image preview
- editable details
- sample table

### 3. Identity Sample Table

Columns:

- `Sample`
- `Kind`
- `Source`
- `Added On`
- `Confidence`
- `Reference`
- `Profile Source`
- `Actions`

Actions:

- `Promote Reference`
- `Set Profile`
- `Delete`

## File Paths Expected To Change

Backend:

- `entrylens-api/setup_supabase.sql`
- `entrylens-api/app/routes/identities.py`
- `entrylens-api/app/schemas/identity.py`
- `entrylens-api/app/supabase.py`

Frontend:

- `entrylens-frontend/src/api/identities.ts`
- `entrylens-frontend/src/pages/PeoplePage.tsx`
- `entrylens-frontend/src/components/Layout.tsx`
- `entrylens-frontend/src/App.tsx`
- `entrylens-frontend/src/styles.css`

Docs:

- `docs/project-truth/data-model.md`
- `docs/project-truth/runtime-flows.md`
- `docs/project-truth/changelog.md`

## Implementation Steps

1. Normalize the current schema around `Identity` and `IdentitySample` semantics while keeping existing tables.
2. Add create/update identity routes.
3. Add sample metadata columns instead of keeping everything only in `metadata`.
4. Add profile-sample selection flow.
5. Rename UI language from `People` to `Identity` where the operator-facing domain should use that term.
6. Update the identity directory/detail pages to expose create/edit/profile/sample actions.
7. Keep recognition flows separate from identity CRUD.

## Verification Steps

- verify current schema file still exists:
  - [`entrylens-api/setup_supabase.sql`](/d:/Testproject2/VisitorsTrackers/entrylens-api/setup_supabase.sql)
- verify current identity route file exists:
  - [`entrylens-api/app/routes/identities.py`](/d:/Testproject2/VisitorsTrackers/entrylens-api/app/routes/identities.py)
- verify current people detail UI exists:
  - [`entrylens-frontend/src/pages/PeoplePage.tsx`](/d:/Testproject2/VisitorsTrackers/entrylens-frontend/src/pages/PeoplePage.tsx)
- verify current frontend identity client exists:
  - [`entrylens-frontend/src/api/identities.ts`](/d:/Testproject2/VisitorsTrackers/entrylens-frontend/src/api/identities.ts)

## Docs Update Checklist

- [ ] update `docs/project-truth/data-model.md` when schema migration lands
- [ ] update `docs/project-truth/runtime-flows.md` when identity CRUD/sample/profile flows are implemented
- [ ] update `docs/project-truth/changelog.md` after implementation
- [ ] archive this plan to `docs/Planning/old/` when complete




<!-- graphify-links:start -->
## Graph Links

- [[graphify-out/wiki/index|Graphify Wiki]]
- [[graphify-out/GRAPH_REPORT|Graph Report]]
- Related file notes:
  - [[graphify-out/wiki/entrylens-api/app/routes/identities.py|entrylens-api/app/routes/identities.py]]
  - [[graphify-out/wiki/entrylens-api/app/schemas/identity.py|entrylens-api/app/schemas/identity.py]]
  - [[graphify-out/wiki/entrylens-api/app/supabase.py|entrylens-api/app/supabase.py]]
  - [[graphify-out/wiki/entrylens-frontend/src/App.tsx|entrylens-frontend/src/App.tsx]]
  - [[graphify-out/wiki/entrylens-frontend/src/api/identities.ts|entrylens-frontend/src/api/identities.ts]]
  - [[graphify-out/wiki/entrylens-frontend/src/components/Layout.tsx|entrylens-frontend/src/components/Layout.tsx]]
- Related communities:
  - [[graphify-out/wiki/communities/Community 0|Community 0]]
  - [[graphify-out/wiki/communities/Community 1|Community 1]]
  - [[graphify-out/wiki/communities/Community 31|Community 31]]
  - [[graphify-out/wiki/communities/Community 35|Community 35]]
<!-- graphify-links:end -->
