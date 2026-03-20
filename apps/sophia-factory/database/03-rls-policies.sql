-- Sophia AI Factory - RLS Policies
-- Run after schema.sql and seed data

-- ============================================
-- ORGANIZATIONS POLICIES
-- ============================================
DROP POLICY IF EXISTS "Users see own org" ON organizations;
CREATE POLICY "Users see own org"
  ON organizations FOR SELECT
  USING (
    auth.uid() IN (
      SELECT id FROM users WHERE org_id = organizations.id
    )
  );

-- ============================================
-- USERS POLICIES
-- ============================================
DROP POLICY IF EXISTS "Users see own profile" ON users;
CREATE POLICY "Users see own profile"
  ON users FOR SELECT
  USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users insert own profile" ON users;
CREATE POLICY "Users insert own profile"
  ON users FOR INSERT
  WITH CHECK (auth.uid() = id);

-- ============================================
-- PROPOSALS POLICIES
-- ============================================
DROP POLICY IF EXISTS "Org members CRUD proposals" ON proposals;
CREATE POLICY "Org members CRUD proposals"
  ON proposals FOR ALL
  USING (
    auth.uid() IN (
      SELECT id FROM users WHERE org_id = proposals.org_id
    )
  );

-- ============================================
-- BRAND VOICES POLICIES
-- ============================================
DROP POLICY IF EXISTS "Org members CRUD brand voices" ON brand_voices;
CREATE POLICY "Org members CRUD brand voices"
  ON brand_voices FOR ALL
  USING (
    auth.uid() IN (
      SELECT id FROM users WHERE org_id = brand_voices.org_id
    )
  );

-- ============================================
-- TRAINING DOCUMENTS POLICIES
-- ============================================
DROP POLICY IF EXISTS "Org members CRUD training docs" ON training_documents;
CREATE POLICY "Org members CRUD training docs"
  ON training_documents FOR ALL
  USING (
    auth.uid() IN (
      SELECT id FROM users WHERE org_id = training_documents.org_id
    )
  );

-- ============================================
-- TEMPLATES POLICIES
-- ============================================
DROP POLICY IF EXISTS "Public read templates" ON templates;
CREATE POLICY "Public read templates"
  ON templates FOR SELECT
  USING (is_public = true OR auth.uid() IS NOT NULL);

DROP POLICY IF EXISTS "Org members CRUD templates" ON templates;
CREATE POLICY "Org members CRUD templates"
  ON templates FOR ALL
  USING (auth.uid() IS NOT NULL);

-- ============================================
-- VERIFICATION QUERY
-- ============================================
-- Run this to verify all policies are in place:
SELECT
  schemaname,
  tablename,
  policyname,
  permissive,
  roles,
  cmd
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;
