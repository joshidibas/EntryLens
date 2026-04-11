# Database Changelog

All database changes (schema migrations, new tables, etc.) are tracked here.

## 2026-04-11 - v0.1.0

### Added

**Initial schema setup for face recognition:**

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create identities table
CREATE TABLE IF NOT EXISTS public.identities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'visitor',
    provider_subject_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create embeddings table
CREATE TABLE IF NOT EXISTS public.embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    identity_id UUID REFERENCES public.identities(id) ON DELETE CASCADE,
    embedding vector(16),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create match_embeddings function
CREATE OR REPLACE FUNCTION public.match_embeddings(query_embedding vector(16), match_limit int DEFAULT 5)
RETURNS TABLE(identity_id UUID, similarity float)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT e.identity_id, 1 - (e.embedding <=> query_embedding) AS similarity
    FROM public.embeddings e
    ORDER BY e.embedding <=> query_embedding
    LIMIT match_limit;
END
$$;
```

**Purpose:** Stores enrolled identities and their face embeddings for local recognition via Labs.

**Source:** `entrylens-api/setup_supabase.sql`

---

## Future Changes (Planned)

### v0.2.0 - Attendance Logging
```sql
CREATE TABLE public.attendance_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    identity_id UUID REFERENCES public.identities(id),
    camera_id TEXT,
    confidence FLOAT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### v0.3.0 - Visitor Logs
```sql
CREATE TABLE public.visitors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    organization TEXT,
    check_in TIMESTAMP WITH TIME ZONE,
    check_out TIMESTAMP WITH TIME ZONE
);
```