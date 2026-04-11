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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
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

-- Test the setup
-- INSERT INTO public.identities (name, role) VALUES ('test', 'visitor');