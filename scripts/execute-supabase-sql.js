#!/usr/bin/env node
/**
 * WellNexus Supabase SQL Executor
 * Executes the e-commerce setup SQL via Supabase Management API
 * 
 * Usage: node execute-supabase-sql.js
 * 
 * Required env vars or hardcoded:
 * - SUPABASE_URL
 * - SUPABASE_SERVICE_ROLE_KEY
 * - SUPABASE_DB_PASSWORD (if using direct connection)
 */

const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');
const path = require('path');

// Configuration - UPDATE THESE VALUES
const SUPABASE_URL = 'https://zumgrvmwmpstsigefuau.supabase.co';
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY || 'YOUR_SERVICE_ROLE_KEY_HERE';
const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp1bWdydm13bXBzdHNpZ2VmdWF1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzg2NzY0MjMsImV4cCI6MjA1NDI1MjQyM30.UU2L5j6V61xM_CfnW0nV3PvkBKWqSGqHxzv3FBhyD2Y';

// SQL Statements to execute (extracted from docs/supabase-ecommerce-setup.sql)
const SQL_STATEMENTS = [
  {
    name: 'get_downline_tree function',
    sql: `
CREATE OR REPLACE FUNCTION get_downline_tree(root_user_id UUID)
RETURNS TABLE (
  id UUID,
  sponsor_id UUID,
  email TEXT,
  name TEXT,
  created_at TIMESTAMP WITH TIME ZONE,
  level INTEGER,
  rank TEXT,
  avatar_url TEXT,
  total_sales BIGINT,
  kyc_status BOOLEAN
) AS $$
WITH RECURSIVE downline AS (
  SELECT
    u.id, u.sponsor_id, u.email, u.name, u.created_at, 1 AS level,
    CASE
      WHEN u.role_id = 1 THEN 'Chủ tịch'
      WHEN u.role_id = 2 THEN 'Đại sứ Diamond'
      WHEN u.role_id = 3 THEN 'Đại sứ Platinum'
      WHEN u.role_id = 4 THEN 'Đại sứ Gold'
      WHEN u.role_id = 5 THEN 'Giám đốc'
      WHEN u.role_id = 6 THEN 'Quản lý'
      WHEN u.role_id = 7 THEN 'Nhân viên'
      WHEN u.role_id = 8 THEN 'CTV'
      ELSE 'Member'
    END AS rank,
    u.avatar_url,
    COALESCE(u.total_sales, 0) AS total_sales,
    COALESCE(u.kyc_status, false) AS kyc_status
  FROM users u WHERE u.sponsor_id = root_user_id
  UNION ALL
  SELECT
    u.id, u.sponsor_id, u.email, u.name, u.created_at, d.level + 1,
    CASE
      WHEN u.role_id = 1 THEN 'Chủ tịch'
      WHEN u.role_id = 2 THEN 'Đại sứ Diamond'
      WHEN u.role_id = 3 THEN 'Đại sứ Platinum'
      WHEN u.role_id = 4 THEN 'Đại sứ Gold'
      WHEN u.role_id = 5 THEN 'Giám đốc'
      WHEN u.role_id = 6 THEN 'Quản lý'
      WHEN u.role_id = 7 THEN 'Nhân viên'
      WHEN u.role_id = 8 THEN 'CTV'
      ELSE 'Member'
    END AS rank,
    u.avatar_url,
    COALESCE(u.total_sales, 0) AS total_sales,
    COALESCE(u.kyc_status, false) AS kyc_status
  FROM users u INNER JOIN downline d ON u.sponsor_id = d.id WHERE d.level < 7
) SELECT * FROM downline ORDER BY level, created_at;
$$ LANGUAGE SQL STABLE;
    `
  },
  {
    name: 'grant get_downline_tree',
    sql: `
GRANT EXECUTE ON FUNCTION get_downline_tree(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION get_downline_tree(UUID) TO anon;
    `
  },
  {
    name: 'distribute_commissions function',
    sql: `
CREATE OR REPLACE FUNCTION distribute_commissions(buyer_user_id UUID, order_amount BIGINT)
RETURNS VOID AS $$
DECLARE
  current_user_id UUID;
  current_level INTEGER := 1;
  commission_rate DECIMAL;
  commission_amount BIGINT;
BEGIN
  SELECT sponsor_id INTO current_user_id FROM users WHERE id = buyer_user_id;
  WHILE current_user_id IS NOT NULL AND current_level <= 7 LOOP
    commission_rate := CASE current_level
      WHEN 1 THEN 0.10 WHEN 2 THEN 0.05 WHEN 3 THEN 0.03
      WHEN 4 THEN 0.02 WHEN 5 THEN 0.01 WHEN 6 THEN 0.005 WHEN 7 THEN 0.003 ELSE 0
    END;
    commission_amount := FLOOR(order_amount * commission_rate);
    INSERT INTO transactions (user_id, amount, type, status, currency, created_at, metadata)
    VALUES (current_user_id, commission_amount, 'commission', 'completed', 'VND', NOW(),
      jsonb_build_object('source_order_user_id', buyer_user_id, 'order_amount', order_amount,
        'commission_level', 'F' || current_level, 'commission_rate', commission_rate));
    UPDATE users SET pending_cashback = COALESCE(pending_cashback, 0) + commission_amount,
      accumulated_bonus_revenue = COALESCE(accumulated_bonus_revenue, 0) + commission_amount
    WHERE id = current_user_id;
    SELECT sponsor_id INTO current_user_id FROM users WHERE id = current_user_id;
    current_level := current_level + 1;
  END LOOP;
END;
$$ LANGUAGE plpgsql;
    `
  },
  {
    name: 'trigger_commission_on_order function',
    sql: `
CREATE OR REPLACE FUNCTION trigger_commission_on_order()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.status = 'completed' AND (OLD.status IS NULL OR OLD.status = 'pending') THEN
    IF NEW.type = 'sale' AND NEW.user_id IS NOT NULL THEN
      PERFORM distribute_commissions(NEW.user_id, NEW.amount);
    END IF;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
    `
  },
  {
    name: 'order_completion_trigger',
    sql: `
DROP TRIGGER IF EXISTS order_completion_trigger ON transactions;
CREATE TRIGGER order_completion_trigger
AFTER UPDATE ON transactions
FOR EACH ROW EXECUTE FUNCTION trigger_commission_on_order();
    `
  },
  {
    name: 'withdrawal_requests table',
    sql: `
CREATE TABLE IF NOT EXISTS withdrawal_requests (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  amount BIGINT NOT NULL CHECK (amount > 0),
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'completed', 'cancelled')),
  bank_name TEXT NOT NULL,
  bank_account_number TEXT NOT NULL,
  bank_account_name TEXT NOT NULL,
  requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  processed_at TIMESTAMP WITH TIME ZONE,
  processed_by UUID REFERENCES users(id),
  rejection_reason TEXT,
  notes TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
    `
  },
  {
    name: 'withdrawal_requests RLS',
    sql: `
ALTER TABLE withdrawal_requests ENABLE ROW LEVEL SECURITY;
    `
  },
  {
    name: 'withdrawal RLS policies',
    sql: `
DROP POLICY IF EXISTS "Users can view own withdrawals" ON withdrawal_requests;
CREATE POLICY "Users can view own withdrawals" ON withdrawal_requests FOR SELECT USING (auth.uid() = user_id);
DROP POLICY IF EXISTS "Users can create withdrawals" ON withdrawal_requests;
CREATE POLICY "Users can create withdrawals" ON withdrawal_requests FOR INSERT WITH CHECK (auth.uid() = user_id);
DROP POLICY IF EXISTS "Admins can update withdrawals" ON withdrawal_requests;
CREATE POLICY "Admins can update withdrawals" ON withdrawal_requests FOR UPDATE
  USING (EXISTS (SELECT 1 FROM users WHERE users.id = auth.uid() AND users.role_id IN (1, 2, 5)));
    `
  },
  {
    name: 'create_withdrawal_request function',
    sql: `
CREATE OR REPLACE FUNCTION create_withdrawal_request(
  p_amount BIGINT, p_bank_name TEXT, p_bank_account_number TEXT, p_bank_account_name TEXT
) RETURNS UUID AS $$
DECLARE
  v_user_id UUID;
  v_available_balance BIGINT;
  v_request_id UUID;
BEGIN
  v_user_id := auth.uid();
  IF v_user_id IS NULL THEN RAISE EXCEPTION 'User not authenticated'; END IF;
  SELECT COALESCE(pending_cashback, 0) INTO v_available_balance FROM users WHERE id = v_user_id;
  IF v_available_balance < p_amount THEN
    RAISE EXCEPTION 'Insufficient balance. Available: %, Requested: %', v_available_balance, p_amount;
  END IF;
  IF p_amount < 2000000 THEN RAISE EXCEPTION 'Minimum withdrawal amount is 2,000,000 VND'; END IF;
  INSERT INTO withdrawal_requests (user_id, amount, bank_name, bank_account_number, bank_account_name, status)
  VALUES (v_user_id, p_amount, p_bank_name, p_bank_account_number, p_bank_account_name, 'pending')
  RETURNING id INTO v_request_id;
  UPDATE users SET pending_cashback = pending_cashback - p_amount WHERE id = v_user_id;
  RETURN v_request_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
    `
  },
  {
    name: 'grant create_withdrawal_request',
    sql: `GRANT EXECUTE ON FUNCTION create_withdrawal_request(BIGINT, TEXT, TEXT, TEXT) TO authenticated;`
  },
  {
    name: 'process_withdrawal_request function',
    sql: `
CREATE OR REPLACE FUNCTION process_withdrawal_request(p_request_id UUID, p_action TEXT, p_notes TEXT DEFAULT NULL)
RETURNS VOID AS $$
DECLARE
  v_admin_id UUID;
  v_request RECORD;
BEGIN
  v_admin_id := auth.uid();
  IF v_admin_id IS NULL THEN RAISE EXCEPTION 'User not authenticated'; END IF;
  IF NOT EXISTS (SELECT 1 FROM users WHERE id = v_admin_id AND role_id IN (1, 2, 5)) THEN
    RAISE EXCEPTION 'Only admins can process withdrawal requests';
  END IF;
  SELECT * INTO v_request FROM withdrawal_requests WHERE id = p_request_id;
  IF NOT FOUND THEN RAISE EXCEPTION 'Withdrawal request not found'; END IF;
  IF v_request.status != 'pending' THEN
    RAISE EXCEPTION 'Withdrawal request is not pending (current status: %)', v_request.status;
  END IF;
  IF p_action = 'approve' THEN
    UPDATE withdrawal_requests SET status = 'approved', processed_at = NOW(), processed_by = v_admin_id, notes = p_notes
    WHERE id = p_request_id;
  ELSIF p_action = 'reject' THEN
    UPDATE withdrawal_requests SET status = 'rejected', processed_at = NOW(), processed_by = v_admin_id, rejection_reason = p_notes
    WHERE id = p_request_id;
    UPDATE users SET pending_cashback = COALESCE(pending_cashback, 0) + v_request.amount WHERE id = v_request.user_id;
  ELSE
    RAISE EXCEPTION 'Invalid action. Use "approve" or "reject"';
  END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
    `
  },
  {
    name: 'grant process_withdrawal_request',
    sql: `GRANT EXECUTE ON FUNCTION process_withdrawal_request(UUID, TEXT, TEXT) TO authenticated;`
  },
  {
    name: 'performance indexes',
    sql: `
CREATE INDEX IF NOT EXISTS idx_users_sponsor_id ON users(sponsor_id);
CREATE INDEX IF NOT EXISTS idx_withdrawal_requests_user_id ON withdrawal_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_withdrawal_requests_status ON withdrawal_requests(status);
CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);
    `
  }
];

async function executeSQLViaREST(sql, supabaseUrl, serviceRoleKey) {
  const response = await fetch(`${supabaseUrl}/rest/v1/rpc/`, {
    method: 'POST',
    headers: {
      'apikey': serviceRoleKey,
      'Authorization': `Bearer ${serviceRoleKey}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ sql })
  });
  return response;
}

async function executeSQLViaPgRest(sql, projectRef, serviceRoleKey) {
  // Use Supabase Management API to execute SQL
  const managementUrl = `https://api.supabase.com/v1/projects/${projectRef}/database/query`;
  
  const response = await fetch(managementUrl, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${serviceRoleKey}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ query: sql })
  });
  
  return response;
}

async function main() {
  console.log('🚀 WellNexus Supabase SQL Executor');
  console.log('='.repeat(50));
  
  // Check for service role key
  if (!SUPABASE_SERVICE_ROLE_KEY || SUPABASE_SERVICE_ROLE_KEY === 'YOUR_SERVICE_ROLE_KEY_HERE') {
    console.log('\n⚠️  Service Role Key not configured!');
    console.log('\n📋 MANUAL INSTRUCTIONS:');
    console.log('1. Go to: https://supabase.com/dashboard/project/zumgrvmwmpstsigefuau/settings/api');
    console.log('2. Copy the "service_role" key (NOT the anon key)');
    console.log('3. Run: SUPABASE_SERVICE_ROLE_KEY="your-key" node execute-supabase-sql.js');
    console.log('\n📋 OR paste the SQL directly in SQL Editor:');
    console.log('   https://supabase.com/dashboard/project/zumgrvmwmpstsigefuau/sql/new');
    
    // Print summary of SQL to execute
    console.log('\n📝 SQL Statements to execute:');
    SQL_STATEMENTS.forEach((stmt, i) => {
      console.log(`   ${i + 1}. ${stmt.name}`);
    });
    
    return;
  }
  
  const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, {
    auth: { persistSession: false }
  });
  
  let successCount = 0;
  let failCount = 0;
  
  for (const statement of SQL_STATEMENTS) {
    console.log(`\n📦 Executing: ${statement.name}...`);
    
    try {
      // Use raw SQL execution via postgres extension or rpc
      const { data, error } = await supabase.rpc('exec_sql', { sql: statement.sql });
      
      if (error) {
        // Fallback: try direct query if rpc not available
        console.log(`   ⚠️ RPC failed, trying direct... (${error.message})`);
        
        // For functions/triggers, we need to use SQL directly
        // This will only work with proper service_role permissions
        throw new Error('Direct SQL execution requires Management API or psql');
      }
      
      console.log(`   ✅ Success: ${statement.name}`);
      successCount++;
    } catch (err) {
      console.log(`   ❌ Failed: ${err.message}`);
      failCount++;
    }
  }
  
  console.log('\n' + '='.repeat(50));
  console.log(`📊 Results: ${successCount} succeeded, ${failCount} failed`);
  
  if (failCount > 0) {
    console.log('\n💡 For failed statements, paste SQL directly in SQL Editor:');
    console.log('   https://supabase.com/dashboard/project/zumgrvmwmpstsigefuau/sql/new');
  }
}

main().catch(console.error);
