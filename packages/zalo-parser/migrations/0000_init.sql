CREATE TABLE IF NOT EXISTS leads (
  id TEXT PRIMARY KEY,
  zalo_user_id TEXT UNIQUE NOT NULL,
  name TEXT,
  phone TEXT,
  interest_area TEXT,
  interest_price TEXT,
  intent TEXT CHECK(intent IN ('warm', 'cold', 'junk', NULL)),
  last_message TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
