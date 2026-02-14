# OpenAI 800M Users Scaling Rules (Unsharded Postgres)
> **Binh Pháp Mapping: The Art of Unsharded Database War**
> Based on "10 Database Scaling Rules OpenAI Broke" (Medium) and OpenAI's Azure Postgres Architecture.

OpenAI scaled ChatGPT to 800M users using a **Single Primary** Postgres instance. This defies conventional "Microservices Sharding" wisdom.
Here is the **Binh Phap Mapping** for AgencyOS/Mekong to achieve similar "smoothness" (mượt).

---

## Rule 1: Single Primary is the General (Thống Lĩnh)
> **Bin Phap Chapter 1: Calculations (Thủy Kế)**
> *“Do not divide your forces unless necessary.”*

*   **OpenAI:** Keeps a single source of truth (Primary) to avoid distributed transaction complexity.
*   **Binh Phap Mapping:** **Centralized Command**. Don't shard prematurely. Sharding introduces exponential complexity (latency, consistency).
*   **AgencyOS Strategy:** Stick to a Monolith Postgres (Supabase/Neon) until vertical scaling hits the wall. Focus on **Read Replicas** instead of Sharding.

## Rule 2: Optimize for Read Heavy (95% Workload)
> **Binh Phap Chapter 6: Weak Points & Strong Points (Hư Thực)**
> *“Appear at points which the enemy must hasten to defend; march swiftly to places where you are not expected.”*

*   **OpenAI:** 95% of traffic is Reads. They optimized strictly for Reads using **Read Replicas**.
*   **Binh Phap Mapping:** **Strike the Void (Hư)**. Offload the heavy reading to cheap replicas. Protect the Real (Primary/Thực) for critical writes only.
*   **AgencyOS Strategy:** Use Supabase Read Replicas for all public/GET APIs.

## Rule 3: Minimize Writes (The Shield)
> **Binh Phap Chapter 4: Tactical Dispositions (Hình)**
> *“To be unconquerable lies with yourself.”*

*   **OpenAI:** Writes are the bottleneck. They offload logs/analytics to CosmosDB/Data Lake.
*   **Binh Phap Mapping:** **Defense First**. Don't let non-critical data (logs, traces, analytics) touch the Primary General.
*   **AgencyOS Strategy:** Move Logs/Audits to Redis or ClickHouse (Tinybird). Do not `INSERT` logs into Postgres Primary.

## Rule 4: PgBouncer is the Gatekeeper (Thủ Môn)
> **Binh Phap Chapter 8: Variation in Tactics (Cửu Biến)**
> *“There are roads which must not be followed.”*

*   **OpenAI:** Uses PgBouncer to pool connections. Raw connections are forbidden.
*   **Binh Phap Mapping:** **Choke Point Control**. Never let the enemy (client requests) flood the General directly.
*   **AgencyOS Strategy:** Supabase Transaction Mode (Port 6543) is mandatory for Serverless Functions.

## Rule 5: Aggressive Caching & Cache Locking
> **Binh Phap Chapter 5: Energy (Binh Thế)**
> *“The onset of troops is like the rush of a torrent which will even roll stones along in its course.”*

*   **OpenAI:** Caches everything. Uses **Cache Locking** (Leasing) to prevent "Thundering Herd" (Cache Stampede) when a key expires.
*   **AgencyOS Strategy:** Implement **Stale-While-Revalidate** in Next.js + Redis Lock for heavy computations.

## Rule 6: No Complex Joins (Speed is Life)
> **Binh Phap Chapter 2: Waging War (Tác Chiến)**
> *“In war, let your great object be victory, not lengthy campaigns.”*

*   **OpenAI:** Avoids heavy JOINs. Prefer simple key-value lookups or denormalized data.
*   **AgencyOS Strategy:** Use **JSONB** for flexibility but avoid deep JSON filtering. Denormalize counters (e.g., `total_likes`) instead of `COUNT(*)` on the fly.

## Rule 7: Workload Isolation (Bulk vs Interactive)
> **Binh Phap Chapter 3: Attack by Stratagem (Mưu Công)**
> *“Divide and conquer.”*

*   **OpenAI:** Separates "Interactive Traffic" (ChatGPT User) from "Bulk Traffic" (Training/Analytics).
*   **AgencyOS Strategy:** Use distinct Roles/Queues for User Actions vs Background Jobs (OpenClaw).

## Rule 8: Strict Schema Governance (Law & Order)
> **Binh Phap Chapter 9: The Army on the March (Hành Quân)**
> *“Soldiers must be treated with humanity, but kept under control by iron discipline.”*

*   **OpenAI:** No table rewrites. No long locks. Migrations must be instant.
*   **AgencyOS Strategy:** Zero-downtime migrations only. Add columns as nullable first.

## Rule 9: Short Timeouts (Fail Fast)
> **Binh Phap Chapter 7: Maneuvering (Quân Tranh)**
> *“Let your rapidity be that of the wind.”*

*   **OpenAI:** Kills slow queries instantly. Better to fail one request than clog the DB.
*   **AgencyOS Strategy:** Set `statement_timeout` to 2s for web requests.

## Rule 10: Operational Discipline (The Way/Đạo)
> **Binh Phap Chapter 1: Laying Plans (Thủy Kế)**
> *“The Moral Law causes the people to be in complete accord with their ruler.”*

*   **OpenAI:** Metrics, Observability, and rigorously tested backup/restore.
*   **Binh Phap Mapping:** **The Tao (Đạo)**. The system must be observable and predictable.
*   **AgencyOS Strategy:** Dashboard monitoring for Query Latency (P99).
