# EntryLens Database Schema

## Overview

This document describes the database schema for the EntryLens application. All tables are hosted on Supabase PostgreSQL with pgvector for face embedding storage.

## Tables

### public.identities

Stores enrolled people (staff/visitors).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique identifier |
| name | TEXT | NOT NULL | Person's name |
| role | TEXT | NOT NULL DEFAULT 'visitor' | 'staff' or 'visitor' |
| provider_subject_id | TEXT | NULLABLE | Reference to external provider |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Creation timestamp |

### public.embeddings

Stores face embedding vectors for recognition.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique identifier |
| identity_id | UUID | REFERENCES identities(id) ON DELETE CASCADE | Foreign key to identities |
| embedding | vector(16) | NOT NULL | 16-dimensional face embedding from MediaPipe |
| metadata | JSONB | NULLABLE | Additional data (name, role, etc.) |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Creation timestamp |

**Note:** The embedding is vector(16) because it uses MediaPipe's facial transformation matrix (4x4 = 16 values).

## Functions

### public.match_embeddings(query_embedding vector(16), match_limit int DEFAULT 5)

Performs cosine similarity search against stored embeddings.

**Returns:** Table of (identity_id UUID, similarity float)

**Usage:**
```sql
SELECT * FROM public.match_embeddings('[0.1, 0.2, ...]', 5);
```

## Relationships

```
identities (1) ←→ (N) embeddings
```

## Indexes

No custom indexes defined yet. Consider adding for performance:
- Index on identities.role for filtering by role
- Index on embeddings.identity_id for join performance

## Future Tables (Planned)

- `public.attendance_logs` - attendance records with timestamps
- `public.visitors` - visitor log entries
- `public.camera_config` - camera settings and locations