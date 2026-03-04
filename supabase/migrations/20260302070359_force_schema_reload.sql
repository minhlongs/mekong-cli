-- Verify contact_submissions exists, re-create if not
CREATE TABLE IF NOT EXISTS public.contact_submissions (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  name text NOT NULL,
  email text NOT NULL,
  message text NOT NULL,
  submitted_at timestamptz DEFAULT now()
);

ALTER TABLE public.contact_submissions ENABLE ROW LEVEL SECURITY;

-- Safely create policies (drop if exists first)
DO $$ BEGIN
  DROP POLICY IF EXISTS "Allow anon insert" ON public.contact_submissions;
  CREATE POLICY "Allow anon insert" ON public.contact_submissions
    FOR INSERT TO anon WITH CHECK (true);
EXCEPTION WHEN OTHERS THEN NULL;
END $$;

DO $$ BEGIN
  DROP POLICY IF EXISTS "Allow service read" ON public.contact_submissions;
  CREATE POLICY "Allow service read" ON public.contact_submissions
    FOR SELECT TO service_role USING (true);
EXCEPTION WHEN OTHERS THEN NULL;
END $$;

-- Force PostgREST schema cache reload
NOTIFY pgrst, 'reload schema';
