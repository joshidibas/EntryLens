# EntryLens Database Schema

## Overview

This document describes the current database schema direction for the EntryLens application. Tables are hosted on Supabase PostgreSQL with pgvector for face embedding storage.

## Tables

### public.identities

Stores the canonical identity record used by admin CRUD.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique identifier |
| name | TEXT | NOT NULL | Legacy display name column kept for compatibility |
| role | TEXT | NOT NULL DEFAULT 'visitor' | Legacy identity type column kept for compatibility |
| display_name | TEXT | NULLABLE | Primary editable display name for CRUD flows |
| identity_type | TEXT | NULLABLE | Primary editable identity type for CRUD flows |
| status | TEXT | NOT NULL DEFAULT 'active' | Identity lifecycle status |
| notes | TEXT | NULLABLE | Operator/admin notes |
| profile_sample_id | UUID | NULLABLE, REFERENCES embeddings(id) ON DELETE SET NULL | Main reference/profile sample |
| provider_subject_id | TEXT | NULLABLE | Reference to external provider |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | NOT NULL DEFAULT NOW() | Last update timestamp |

### public.embeddings

Stores per-identity face samples and their embeddings.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique identifier |
| identity_id | UUID | REFERENCES identities(id) ON DELETE CASCADE | Foreign key to identities |
| embedding | vector(16) | NOT NULL | 16-dimensional face embedding from MediaPipe |
| metadata | JSONB | NULLABLE | Legacy metadata bag kept for compatibility |
| sample_kind | TEXT | NOT NULL DEFAULT 'face' | Sample type |
| image_path | TEXT | NULLABLE | Stored path or object key for the source image |
| capture_source | TEXT | NULLABLE | Source of the sample |
| capture_confidence | DOUBLE PRECISION | NULLABLE | Confidence recorded during capture/review |
| is_reference | BOOLEAN | NOT NULL DEFAULT false | Preferred matching/reference sample |
| is_profile_source | BOOLEAN | NOT NULL DEFAULT false | Sample selected as the main profile image |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | NOT NULL DEFAULT NOW() | Last update timestamp |

**Note:** The embedding is still `vector(16)` because the current implementation uses MediaPipe facial transformation output as a placeholder vector.

## Functions

### public.match_embeddings(query_embedding vector(16), match_limit int DEFAULT 5)

Performs cosine similarity search against stored embeddings.

**Returns:** Table of `(identity_id UUID, similarity float)`

**Usage:**
```sql
SELECT * FROM public.match_embeddings('[0.1, 0.2, ...]', 5);
```

## Relationships

```text
identities (1) <-> (N) embeddings
identities.profile_sample_id -> embeddings.id
```

## Indexes

The migrated schema should include these helpful indexes:

- index on `identities.display_name`
- index on `identities.identity_type`
- index on `identities.status`
- index on `embeddings.identity_id`
- partial unique index ensuring one `is_profile_source = true` row per identity
- partial unique index ensuring one `is_reference = true` row per identity

## CRUD Model Notes

The intended application model is now:

- `identities` is the canonical person record used by admin CRUD
- `embeddings` functions as the current identity-samples table
- `profile_sample_id` points to the one sample that should be shown as the main ref/profile image
- `is_profile_source` and `is_reference` remain useful sample-level flags for operator workflow
- sample images can currently be stored on disk under `runtime-data/identity-samples/` with the relative file path saved in `embeddings.image_path`

The legacy `name`, `role`, and `metadata` fields remain so the codebase can transition safely, but new code should prefer:

- `display_name` over `name`
- `identity_type` over `role`
- first-class sample columns over `metadata`

## Future Tables (Planned)

- `public.attendance_logs` - attendance records with timestamps
- `public.visitors` - visitor log entries
- `public.camera_config` - camera settings and locations
