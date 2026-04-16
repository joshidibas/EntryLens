-- Supabase SQL Setup for EntryLens Face Recognition
-- Run this in Supabase Dashboard → SQL Editor

-- Enable pgvector extension (required for vector storage)
CREATE EXTENSION IF NOT EXISTS vector;

-- Create identities table (stores enrolled people)
CREATE TABLE IF NOT EXISTS public.identities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'visitor',
    provider_subject_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create embeddings table (stores face embeddings)
CREATE TABLE IF NOT EXISTS public.embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    identity_id UUID REFERENCES public.identities(id) ON DELETE CASCADE,
    embedding vector(16),
    metadata JSONB,
    model_id TEXT NOT NULL DEFAULT 'local-default',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create InsightFace embeddings table (stores backend-hosted InsightFace vectors)
CREATE TABLE IF NOT EXISTS public.insightface_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    identity_id UUID REFERENCES public.identities(id) ON DELETE CASCADE,
    embedding vector(512),
    model_id TEXT NOT NULL DEFAULT 'insightface-local',
    metadata JSONB,
    sample_kind TEXT NOT NULL DEFAULT 'face',
    image_path TEXT,
    capture_source TEXT,
    capture_confidence DOUBLE PRECISION,
    is_reference BOOLEAN NOT NULL DEFAULT false,
    is_profile_source BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create match_embeddings function (cosine similarity search)
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

CREATE OR REPLACE FUNCTION public.match_insightface_embeddings(query_embedding vector(512), match_limit int DEFAULT 5)
RETURNS TABLE(identity_id UUID, similarity float)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT e.identity_id, 1 - (e.embedding <=> query_embedding) AS similarity
    FROM public.insightface_embeddings e
    ORDER BY e.embedding <=> query_embedding
    LIMIT match_limit;
END
$$;

-- Test the setup
-- INSERT INTO public.identities (name, role) VALUES ('test', 'visitor');
