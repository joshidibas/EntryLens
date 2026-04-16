# Plan: Detection Logs And Unknown Identity Merge

## Task Summary

Add a new `detection_logs` workflow driven only from the Live feed.

When a face is detected:

- if recognition confidence is `>= 0.95`, create a detection log tagged to the matched identity
- if the face cannot be confidently identified, create a detection log and also create a placeholder unknown identity for that detection

From the detection-log detail page, the operator must be able to:

- rename the placeholder into a new real identity
- or merge/link it into an already existing identity
- if linked to an existing identity, the temporary placeholder identity should be removed afterward
- create or attach the detection embedding into the identity-sample store during review

This is explicitly a `detection_logs` feature, not `visitor_logs`.

## Current Repo Truth

Verified current implementation state:

- Identity CRUD exists in:
  [`entrylens-api/app/routes/identities.py`](/d:/Testproject2/VisitorsTrackers/entrylens-api/app/routes/identities.py)
- Identity/sample data access exists in:
  [`entrylens-api/app/supabase.py`](/d:/Testproject2/VisitorsTrackers/entrylens-api/app/supabase.py)
- The current live recognition flow is frontend-driven and shared through:
  [`entrylens-frontend/src/hooks/useRecognitionSession.ts`](/d:/Testproject2/VisitorsTrackers/entrylens-frontend/src/hooks/useRecognitionSession.ts)
- The current live camera experience is rendered through:
  [`entrylens-frontend/src/components/CameraPanel.tsx`](/d:/Testproject2/VisitorsTrackers/entrylens-frontend/src/components/CameraPanel.tsx)
- Current identity sample images are stored locally under:
  `runtime-data/identity-samples/`
- The current embedding used for matching is still the placeholder `vector(16)` MediaPipe transform output
- There is no `detection_logs` table or route family yet

## Key Product Rules

### 1. Live Feed Is The Only Writer

New detection logs are created only from the Live feed flow.

Not from:

- Labs
- Add Data page
- Identity detail page
- Enrollment page

### 2. Auto-Tag Rule

If the best recognition confidence is `>= 0.95`:

- create a `detection_logs` row
- set auto-tag fields to the matched identity

If confidence is below `0.95` or no identity matches:

- still create a `detection_logs` row
- create a placeholder unknown identity for this detection
- link the detection to that placeholder

### 3. Duplicate Suppression

Do not create repeated detection logs in rapid succession.

Recommended default window:

- `15 seconds`

Suppress if:

- same recognized identity was just logged recently from Live feed
- or same unknown-face signature was just logged recently from Live feed

This should be enforced in backend app logic before insert, not only by frontend logic.

### 4. Unknown Placeholder Review Flow

If a placeholder unknown identity is created:

- the detection detail page must allow the operator to rename it into a new real identity
- or merge it into an existing identity

When merging into an existing identity:

- move the relevant links/samples from the placeholder identity to the chosen existing identity
- delete the temporary placeholder identity

## Recommended Schema

### Detection Log Meaning

One row represents one saved Live-feed detection event.

It should preserve:

- the snapshot image
- the placeholder embedding
- automatic recognition result at save time
- the identity currently linked to the detection
- review status
- whether the detection embedding was promoted into identity samples

### Unknown Identity Meaning

When the system cannot confidently identify someone, it should create:

- a new placeholder identity row in `identities`
- default `display_name` such as `Unknown 2026-04-11 14:32:18`
- `identity_type = 'unknown'`
- `status = 'pending_review'`

This allows the operator to work against a real identity record immediately.

## SQL To Run

Run this in Supabase SQL editor before backend implementation.

```sql
begin;

alter table public.identities
  add column if not exists review_source text,
  add column if not exists merged_into_identity_id uuid null references public.identities(id) on delete set null;

create index if not exists idx_identities_review_source
  on public.identities (review_source);

create index if not exists idx_identities_merged_into_identity_id
  on public.identities (merged_into_identity_id);

create table if not exists public.detection_logs (
  id uuid primary key default gen_random_uuid(),

  source text not null default 'live-feed',
  camera_id text null,

  image_path text null,
  embedding vector(16) null,
  embedding_signature text null,

  auto_similarity double precision null,
  auto_identity_id uuid null references public.identities(id) on delete set null,
  auto_display_name text null,
  auto_tagged boolean not null default false,

  current_identity_id uuid null references public.identities(id) on delete set null,

  review_status text not null default 'pending',
  review_notes text null,
  reviewed_at timestamptz null,

  promoted_embedding_id uuid null references public.embeddings(id) on delete set null,
  promoted_at timestamptz null,

  detected_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_detection_logs_detected_at
  on public.detection_logs (detected_at desc);

create index if not exists idx_detection_logs_source
  on public.detection_logs (source);

create index if not exists idx_detection_logs_camera_id
  on public.detection_logs (camera_id);

create index if not exists idx_detection_logs_auto_identity_id
  on public.detection_logs (auto_identity_id);

create index if not exists idx_detection_logs_current_identity_id
  on public.detection_logs (current_identity_id);

create index if not exists idx_detection_logs_review_status
  on public.detection_logs (review_status);

create index if not exists idx_detection_logs_embedding_signature
  on public.detection_logs (embedding_signature);

create or replace function public.set_detection_logs_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists trg_detection_logs_set_updated_at on public.detection_logs;
create trigger trg_detection_logs_set_updated_at
before update on public.detection_logs
for each row
execute function public.set_detection_logs_updated_at();

commit;
```

## Recommended Review Status Values

Use these values in backend/frontend code:

- `pending`
- `auto_tagged`
- `confirmed_new_identity`
- `merged_to_existing`
- `dismissed`

## Suggested Placeholder Unknown Identity Values

When creating the fallback identity:

- `display_name = 'Unknown ' || timestamp`
- `identity_type = 'unknown'`
- `status = 'pending_review'`
- `review_source = 'live-detection'`

## Backend Surface To Build

### Detection log routes

- `POST /api/v1/detection-logs`
  - used only by Live feed
  - performs duplicate suppression
  - creates placeholder unknown identity when needed
- `GET /api/v1/detection-logs`
  - list recent logs
- `GET /api/v1/detection-logs/{id}`
  - detection detail
- `PATCH /api/v1/detection-logs/{id}`
  - save review notes, review status, or rename current placeholder identity
- `POST /api/v1/detection-logs/{id}/merge-identity`
  - move detection/sample references to an existing identity
  - delete placeholder identity
- `POST /api/v1/detection-logs/{id}/promote-sample`
  - create an `embeddings` sample from the stored detection embedding/image

### Required service behavior

- compute `embedding_signature` from a rounded subset of the vector
- if recognized identity exists and same identity logged within 15 seconds, skip insert
- if unknown and same signature logged within 15 seconds, skip insert
- when merging:
  - update `detection_logs.current_identity_id`
  - move any promoted sample ownership if needed
  - mark placeholder identity as merged/deleted

## Frontend Surface To Build

### 1. Detection Logs Page

New page route:

- `/detection-logs`

Columns:

- detected time
- current image
- auto-tag result
- current linked identity
- review status
- actions

### 2. Detection Log Detail Page

New page route:

- `/detection-logs/:logId`

The detail page should show:

- captured image
- auto-tag result and similarity
- current linked identity
- whether the embedding has already been promoted

Actions:

- rename placeholder unknown identity into a real identity
- merge into existing identity
- promote detection embedding as a sample
- optionally set promoted sample as reference/profile

## Files Expected To Change

Backend:

- `entrylens-api/app/routes/`
- `entrylens-api/app/schemas/`
- `entrylens-api/app/supabase.py`
- `entrylens-api/app/main.py`

Frontend:

- `entrylens-frontend/src/App.tsx`
- `entrylens-frontend/src/pages/LivePage.tsx`
- `entrylens-frontend/src/pages/`
- `entrylens-frontend/src/api/`
- `entrylens-frontend/src/components/`
- `entrylens-frontend/src/hooks/`

Docs:

- `docs/database/schema.md`
- `docs/project-truth/data-model.md`
- `docs/project-truth/architecture-truth.md`
- `docs/project-truth/repo-map.md`
- `docs/project-truth/changelog.md`

## Implementation Order

1. Run the SQL above.
2. Add backend schemas and Supabase helpers for `detection_logs`.
3. Build Live-feed-only detection-log writer with duplicate suppression.
4. Add detection-log list/detail routes.
5. Build list/detail frontend pages.
6. Add merge/rename/promote actions in detail page.
7. Update docs once the runtime is real.

## Verification Steps

Once implemented, verify:

1. Live feed creates one detection log for a recognized person at high confidence.
2. Repeated frames of the same person do not create repeated logs inside the debounce window.
3. Unknown face creates both:
   - a detection log
   - a placeholder unknown identity
4. Detection detail page can rename placeholder into a real person.
5. Detection detail page can merge placeholder into an existing identity and delete the temporary identity.
6. Detection detail page can promote the stored detection into a new identity sample.
7. Labs, Enroll, and Add Data pages do not create detection logs.

## Docs Update Checklist

After implementation becomes real, update:

- `docs/database/schema.md`
- `docs/project-truth/data-model.md`
- `docs/project-truth/architecture-truth.md`
- `docs/project-truth/repo-map.md`
- `docs/project-truth/changelog.md`




<!-- graphify-links:start -->
## Graph Links

- [[graphify-out/wiki/index|Graphify Wiki]]
- [[graphify-out/GRAPH_REPORT|Graph Report]]
- Related file notes:
  - [[graphify-out/wiki/entrylens-api/app/main.py|entrylens-api/app/main.py]]
  - [[graphify-out/wiki/entrylens-api/app/routes/identities.py|entrylens-api/app/routes/identities.py]]
  - [[graphify-out/wiki/entrylens-api/app/supabase.py|entrylens-api/app/supabase.py]]
  - [[graphify-out/wiki/entrylens-frontend/src/App.tsx|entrylens-frontend/src/App.tsx]]
  - [[graphify-out/wiki/entrylens-frontend/src/components/CameraPanel.tsx|entrylens-frontend/src/components/CameraPanel.tsx]]
  - [[graphify-out/wiki/entrylens-frontend/src/hooks/useRecognitionSession.ts|entrylens-frontend/src/hooks/useRecognitionSession.ts]]
  - [[graphify-out/wiki/entrylens-frontend/src/pages/LivePage.tsx|entrylens-frontend/src/pages/LivePage.tsx]]
- Related communities:
  - [[graphify-out/wiki/communities/Community 0|Community 0]]
  - [[graphify-out/wiki/communities/Community 2|Community 2]]
  - [[graphify-out/wiki/communities/Community 11|Community 11]]
  - [[graphify-out/wiki/communities/Community 13|Community 13]]
  - [[graphify-out/wiki/communities/Community 31|Community 31]]
<!-- graphify-links:end -->
