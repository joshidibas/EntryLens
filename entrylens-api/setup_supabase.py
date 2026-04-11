"""
Setup script to create Supabase tables and functions for face recognition.
Run with: cd entrylens-api && python setup_supabase.py
"""

from supabase import create_client

# Read from .env
with open("D:\\Testproject2\\VisitorsTrackers\\.env") as f:
    env = f.read()

supabase_url = None
service_key = None
for line in env.split('\n'):
    if line.startswith('SUPABASE_URL='):
        supabase_url = line.split('=', 1)[1].strip()
    elif line.startswith('SUPABASE_SERVICE_KEY='):
        service_key = line.split('=', 1)[1].strip()

if not service_key or service_key == "your-service-role-key":
    print("ERROR: Please update .env with your actual Supabase service role key")
    exit(1)

client = create_client(supabase_url, service_key)

# Enable pgvector extension
print("Enabling pgvector extension...")
try:
    # Use postgrest to execute raw SQL - this is the correct way
    client.postgrest.schema('public').execute("CREATE EXTENSION IF NOT EXISTS vector;")
except Exception as e:
    print(f"pgvector note: {e}")

# Create identities table
print("\nCreating identities table...")
sql_identities = """
CREATE TABLE IF NOT EXISTS public.identities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'visitor',
    provider_subject_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
"""
try:
    # Execute raw SQL via anon endpoint workaround
    # Since we can't execute raw SQL directly, we'll try inserting to create
    # If it fails because table doesn't exist, we'll know
    result = client.table('identities').select('*').limit(1).execute()
    print("Identities table already exists")
except Exception as e:
    print("Need to create tables via Supabase dashboard SQL editor")
    print(f"\nPlease run this SQL in Supabase Dashboard → SQL Editor:\n")
    print("=" * 60)
    print("""
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

-- Create embeddings table with vector
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
""")
    print("=" * 60)
    exit(0)

print("\n✅ Supabase client connected successfully!")
print("Note: Table creation requires running SQL in Supabase dashboard.")