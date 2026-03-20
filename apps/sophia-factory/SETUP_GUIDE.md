# Sophia AI Factory - Setup Checklist

## Completed Steps

- [x] **Step 1: Install Dependencies**
  - `pnpm install` completed successfully
  - All packages installed

- [x] **Step 4: Create .env.local**
  - Copied from `.env.local.example`
  - Located at: `/Users/macbook/mekong-cli/apps/sophia-factory/.env.local`

---

## Your Action Items

### Step 2: Create Supabase Project

1. Go to **[supabase.com](https://supabase.com)** and sign in
2. Click **"New Project"**
3. Fill in:
   | Field | Value |
   |-------|-------|
   | **Name** | `sophia-factory` |
   | **Database Password** | _(create a strong password, save it)_ |
   | **Region** | _(choose nearest to you)_ |
4. Wait ~2 minutes for provisioning

### Step 3: Get API Credentials

After project is ready:

1. Go to **Settings** → **API**
2. Copy these values:
   - **Project URL**: `https://xxxxx.supabase.co`
   - **anon/public key**: `eyJhbGc...` (long string)
   - **service_role key**: _(keep secret, server-side only)_

### Step 4: Run Database Schema

1. Open **SQL Editor** in Supabase Dashboard
2. Copy the content from `/Users/macbook/mekong-cli/apps/sophia-factory/database/schema.sql`
3. Paste into SQL Editor and click **Run**
4. Verify all 6 tables are created

Then run RLS policies from `database/01-setup-guide.md` (lines 55-91).

### Step 5: Update .env.local

Edit `/Users/macbook/mekong-cli/apps/sophia-factory/.env.local`:

```bash
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# OpenAI for AI Features
OPENAI_API_KEY=sk-...your-openai-key

# Application Settings
NEXT_PUBLIC_APP_URL=http://localhost:3000
NODE_ENV=development
```

### Step 6: Verify & Run

```bash
cd /Users/macbook/mekong-cli/apps/sophia-factory
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

---

## File Locations

| File | Path |
|------|------|
| Schema | `/Users/macbook/mekong-cli/apps/sophia-factory/database/schema.sql` |
| Seed Data | `/Users/macbook/mekong-cli/apps/sophia-factory/database/02-seed-data.sql` |
| Setup Guide | `/Users/macbook/mekong-cli/apps/sophia-factory/database/01-setup-guide.md` |
| Env Example | `/Users/macbook/mekong-cli/apps/sophia-factory/.env.local.example` |
| Env (to edit) | `/Users/macbook/mekong-cli/apps/sophia-factory/.env.local` |

---

**Status:** Ready for Supabase setup. Complete Steps 2-5 above, then run `npm run dev`.
