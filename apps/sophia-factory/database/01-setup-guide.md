# Supabase Setup Guide

## Quick Start

### 1. Create Project

1. Go to [supabase.com](https://supabase.com)
2. Click "New Project"
3. Fill in:
   - **Name:** `sophia-factory`
   - **Database Password:** (save securely)
   - **Region:** Choose nearest to you
4. Wait ~2 minutes for provisioning

### 2. Run Schema

1. Open **SQL Editor** in Supabase Dashboard
2. Copy entire content from `schema.sql`
3. Paste and click **Run**
4. Verify: All tables created successfully

### 3. Enable pgvector

In SQL Editor, run:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 4. Get Credentials

Go to **Settings** → **API**:

- **Project URL:** `https://xxxxx.supabase.co`
- **anon/public key:** `eyJhbGc...` (long string)
- **service_role key:** (keep secret, for server-side only)

### 5. Configure Environment

Copy `.env.local.example` to `.env.local`:

```bash
cp .env.local.example .env.local
```

Fill in values from Step 4.

### 6. Verify Connection

```bash
npm run db:check
```

## RLS Policies

After schema is applied, run these policies in SQL Editor:

```sql
-- Organizations: Users can see their own org
CREATE POLICY "Users see own org"
  ON organizations FOR SELECT
  USING (auth.uid() IN (SELECT id FROM users WHERE org_id = organizations.id));

-- Users: Can see own profile
CREATE POLICY "Users see own profile"
  ON users FOR SELECT
  USING (auth.uid() = id);

-- Proposals: Org members can CRUD
CREATE POLICY "Org members CRUD proposals"
  ON proposals FOR ALL
  USING (auth.uid() IN (SELECT id FROM users WHERE org_id = proposals.org_id));

-- Brand Voices: Org members can CRUD
CREATE POLICY "Org members CRUD brand voices"
  ON brand_voices FOR ALL
  USING (auth.uid() IN (SELECT id FROM users WHERE org_id = brand_voices.org_id));

-- Training Documents: Org members can CRUD
CREATE POLICY "Org members CRUD training docs"
  ON training_documents FOR ALL
  USING (auth.uid() IN (SELECT id FROM users WHERE org_id = training_documents.org_id));

-- Templates: Public read, org members write
CREATE POLICY "Public read templates"
  ON templates FOR SELECT
  USING (is_public = true);

CREATE POLICY "Org members CRUD templates"
  ON templates FOR ALL
  USING (true); -- Simplified, add org check if needed
```

## Next Steps

1. Run seed data: `npm run db:seed`
2. Test connection with included script
3. Start development: `npm run dev`
