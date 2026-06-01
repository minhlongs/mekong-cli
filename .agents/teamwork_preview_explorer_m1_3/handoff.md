# Handoff Report — Security and Reliability Gap Analysis

**From:** Explorer 3  
**Working Directory:** `/Users/macbook/mekong-cli/.agents/teamwork_preview_explorer_m1_3`  
**Status:** Task Complete  

---

## 1. Observation

### 1.1 SQLite Connection Leaks
*   **Source:** `/Users/macbook/mekong-cli/src/raas/tenant.py` (lines 94-99, 134-143):
    ```python
    def _connect(self) -> sqlite3.Connection:
        """Open a WAL-mode connection with row_factory enabled."""
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def create_tenant(self, name: str) -> Tenant:
        ...
        try:
            with self._connect() as conn:
                conn.execute(
                    "INSERT INTO tenants (id, name, api_key_hash, created_at, is_active) "
                    "VALUES (?, ?, ?, ?, 1)",
                    (tenant_id, name, key_hash, created_at),
                )
                conn.commit()
        ...
    ```
*   **Source:** `/Users/macbook/mekong-cli/src/raas/credits.py` (lines 245-264):
    ```python
    def add(self, tenant_id: str, amount: int, reason: str) -> int:
        ...
        try:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO credit_accounts (tenant_id, balance, total_earned, total_spent)
                    ...
    ```

### 1.2 Schema Modification Lock Collision (DDL on Query)
*   **Source:** `/Users/macbook/mekong-cli/apps/nhipdieuxanh-orchestrator/mock-services/ai-service/retriever.py` (lines 26-29):
    ```python
    def init_db(self):
        """Initializes tables if they do not exist (useful for testing/mock)."""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                ...
    ```
*   **Source:** `/Users/macbook/mekong-cli/apps/nhipdieuxanh-orchestrator/mock-services/ai-service/main.py` (lines 147-152):
    ```python
    @app.post("/api/ai/query-agent")
    def query_agent(req: QueryAgentRequest):
        retriever = None
        try:
            retriever = AskPythonRetriever()
            # Retrieve relevant chunks using the new retriever
            chunks = retriever.retrieve(req.question, limit=req.limit)
    ```

### 1.3 Lead Ingestion Race Conditions
*   **Source:** `/Users/macbook/mekong-cli/apps/nhipdieuxanh/app/api/leads/route.ts` (lines 187-228):
    ```typescript
    const existingLead = consent ? await prisma.lead.findFirst({
      where: {
        OR: [
          { leadHash },
          { phone: cleanPhone }
        ]
      }
    }) : null
    ...
    if (existingLead) {
      lead = await prisma.lead.update({ ... })
    } else {
      lead = await prisma.lead.create({ ... })
    }
    ```

### 1.4 API Gateway Rate Limiting Deficiencies
*   **Source:** `/Users/macbook/mekong-cli/apps/nhipdieuxanh-orchestrator/gateway/nginx.conf` (lines 58-69):
    ```nginx
        # Route for Backend Core APIs
        location /api/leads {
            proxy_pass http://backend_service;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Rate limiting / Timeout config
            proxy_connect_timeout 5s;
            proxy_read_timeout 30s;
        }
    ```

### 1.5 Exposed Unlocked Wallet in Blockchain Notarization
*   **Source:** `/Users/macbook/mekong-cli/apps/nhipdieuxanh/lib/blockchain.ts` (lines 13-57):
    ```typescript
    const accountsRes = await fetch(blockchainRpcUrl, {
      method: 'POST',
      body: JSON.stringify({ jsonrpc: '2.0', method: 'eth_accounts', params: [], id: 1 })
    })
    ...
    const fromAccount = accounts[0]
    ...
    const txRes = await fetch(blockchainRpcUrl, {
      method: 'POST',
      body: JSON.stringify({
        jsonrpc: '2.0',
        method: 'eth_sendTransaction',
        params: [{
          from: fromAccount,
          to: '0x0000000000000000000000000000000000000000',
          data: hexPayload
        }],
        id: 2
      })
    })
    ```

### 1.6 Unauthenticated PII Leakage Endpoint
*   **Source:** `/Users/macbook/mekong-cli/apps/nhipdieuxanh/app/api/leads/route.ts` (lines 272-286):
    ```typescript
    export async function GET() {
      try {
        const leads = await prisma.lead.findMany({
          orderBy: { createdAt: 'desc' }
        })
        return NextResponse.json({ success: true, leads })
    ```

### 1.7 Hardcoded API Keys & Production Configs
*   **Source:** `/Users/macbook/mekong-cli/.env` (lines 7-8):
    ```bash
    POLAR_API_KEY=polar_oat_wgwxXaiow4uWlHzzEkF2nG04YhoKi2SeqwM4R2i3jnc
    POLAR_WEBHOOK_SECRET=polar_whs_wDXSPG4aiQBMDGqSWXVor7aEnXEvMY3IdadBN1UvKPE
    ```
*   **Source:** `/Users/macbook/mekong-cli/apps/nhipdieuxanh-orchestrator/helm/nhipdieuxanh/values.yaml` (lines 53-65):
    ```yaml
    database:
      url: "postgresql://postgres:postgres@postgres-service:5432/nhipdieuxanh_db"
    ...
    postgres:
      image: postgres:15-alpine
      port: 5432
      user: postgres
      password: postgres
      db: nhipdieuxanh_db
    ```

---

## 2. Logic Chain

1. **SQLite Connection Leakage**: 
   - *Observation:* `TenantStore._connect` and `CreditStore.add` open SQLite connections in `with` context blocks but never execute `conn.close()`.
   - *Reasoning:* In Python, a `with connection:` block commits/rolls back transactions but keeps the connection open.
   - *Conclusion:* File descriptors accumulate on the RaaS daemon until exhaustion, crashing the gateway service.

2. **SQLite Lock Conflicts**:
   - *Observation:* `query_agent` instantiates `AskPythonRetriever` on every query, which runs `init_db()` containing DDL queries (`CREATE TABLE IF NOT EXISTS`).
   - *Reasoning:* Schema alterations require write locks in SQLite.
   - *Conclusion:* Under concurrent requests, SQLite locks up and throws `database is locked` on simple read operations.

3. **Check-Then-Act Concurrency**:
   - *Observation:* `leads/route.ts` runs a `findFirst` query followed by a `create` or `update` block.
   - *Reasoning:* Concurrent requests for the same lead phone number can bypass `findFirst` concurrently, triggering database-level unique constraint violations (`P2002`) on `create()`.
   - *Conclusion:* Bypassing the transactional outbox pattern or retry queues causes unhandled 500 server errors on the ingestion endpoint.

4. **Broken Access Control & PII Exposure**:
   - *Observation:* `GET /api/leads` is completely unauthenticated and dumps the entire `leads` list containing plaintext names, phone numbers, and emails.
   - *Reasoning:* Accessing sensitive personal information without authorization token checks violates basic OWASP standards.
   - *Conclusion:* The endpoint is fully exposed to public data harvesting, violating Vietnam's Decree 13.

5. **Blockchain Node Wallet Expositions**:
   - *Observation:* `blockchain.ts` uses JSON-RPC `eth_accounts` and `eth_sendTransaction` relying on the Geth node to sign and hold keys.
   - *Reasoning:* Exposing JSON-RPC `8545` with unlocked wallets is a severe security vulnerability that allows direct asset theft.
   - *Conclusion:* Notarization must use local transaction signing with private keys and `eth_sendRawTransaction`.

6. **Hardcoded Credentials & IaC Exposure**:
   - *Observation:* Root `.env` has active `POLAR_API_KEY` and Helm `values.yaml` defaults credentials to `postgres:postgres` for production.
   - *Reasoning:* Hardcoding secrets in git config maps allows anyone with repository or cluster read access to compromise credentials.
   - *Conclusion:* Credentials must be managed via secret-injectors (Vault/Kubernetes Secrets) rather than static Helm values files.

---

## 3. Caveats

- We did not perform a live penetration test or load test on Geth to capture real-time nonce assignment behavior, relying on source code analysis of the JSON-RPC calls.
- We assumed `POLAR_API_KEY` in the root `.env` is active based on prefixing and naming, but did not perform HTTP requests to verify its authorization scopes.
- We did not evaluate the integrity of the private Geth network setup outside the `nhipdieuxanh-orchestrator` project directory.

---

## 4. Conclusion

The codebase contains major security and reliability gaps. While architectural reports claim full production authorization, the existence of public unauthenticated PII endpoints, database connection leaks in core RaaS managers, schema alteration locks on search queries, and exposed Geth unlocked accounts represent significant liabilities. Decoupling SQLite DDL migrations, implementing JWT authentication on lead routes, moving wallet keys to application client instances, and scrubbing hardcoded API tokens are urgent remediation tasks.

---

## 5. Verification Method

- **SQLite Connection Leak:** Run a test loop calling `create_tenant` or `list_tenants` 1000 times, and check open file handles using `lsof -p <PID_OF_DAEMON> | grep tenants.db`. The count will climb continuously if not closed.
- **Unauthenticated PII Exposure:** Run:
  ```bash
  curl -i -X GET http://localhost/api/leads
  ```
  Check that it returns a JSON response containing raw lead names and emails with an HTTP 200 status instead of HTTP 401 Unauthorized.
- **DDL Query Lock:** Simulate concurrent requests on `/api/ai/query-agent` using `ab` or `k6` to observe lock exceptions:
  ```bash
  k6 run tests/performance/load-test.js
  ```
  Inspect FastAPI logs for `sqlite3.OperationalError: database is locked` stack traces.
