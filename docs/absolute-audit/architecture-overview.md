# Architecture Overview

This document describes the package dependency relationships, runtime data flows, and runtime processing steps across the `mekong-cli` monorepo.

---

## 1. Subsystem Dependency Relationships

The diagram below illustrates how internal packages/workspaces and external systems interact:

```mermaid
flowchart TD
    subgraph Apps
        orchestrator[apps/nhipdieuxanh-orchestrator]
        ndx_app[apps/nhipdieuxanh Next.js App]
    end

    subgraph Packages
        mekong_core[packages/mekong-cli-core]
        ask_core[packages/ask-core]
    end

    subgraph External Systems
        postgres[(PostgreSQL Database)]
        kafka[[Apache Kafka Event Bus]]
        geth[Geth Blockchain Node]
        model_server[Model Server Ollama / OpenAI]
    end

    orchestrator -->|IaC / Helm Deploy| ndx_app
    orchestrator -->|IaC / Helm Deploy| postgres
    orchestrator -->|IaC / Helm Deploy| kafka
    orchestrator -->|IaC / Helm Deploy| geth
    
    ndx_app -->|Uses Workspace Reference| ask_core
    ndx_app -->|Read/Write| postgres
    ndx_app -->|Publish Event| kafka
    ndx_app -->|Notarize JSON-RPC| geth

    mekong_core -->|Uses Workspace Reference| ask_core
    mekong_core -->|Call CLI commands| ask_core
    
    ask_core -->|Fetch Embeddings| model_server
    
    orchestrator -->|Runs FastAPI AI Microservice| ai_service[FastAPI AI Service]
    ai_service -->|Subscribe| kafka
    ai_service -->|Write Updates| postgres
    ai_service -->|Query Agent / RAG Search| ask_core
```

---

## 2. Runtime Data Flows

### A. Lead Ingestion Lifecycle

This sequence diagram depicts the flow when a new user registers as a lead, including scoring, masking (Decree 13 compliance), Kafka dispatch, blockchain notarization, and background AI processing.

```mermaid
sequenceDiagram
    autonumber
    actor User as Prospective Buyer
    participant Gateway as Nginx Gateway
    participant Backend as apps/nhipdieuxanh (Next.js)
    participant DB as PostgreSQL
    participant Kafka as Apache Kafka Event Bus
    participant Geth as Geth Blockchain Node
    participant AIService as FastAPI AI Service (Orchestrator)

    User->>Gateway: POST /api/leads
    Gateway->>Backend: Forward request
    
    Note over Backend: Validate phone format<br/>Perform dynamic lead scoring<br/>Segment persona based on keywords
    
    alt User Consent is False (Decree 13 Masking)
        Note over Backend: Mask Name, Phone, Email with asterisks<br/>Generate random UUID as leadHash
    else User Consent is True
        Note over Backend: Hash phone using SHA-256 as leadHash
    end
    
    Backend->>DB: Upsert Lead status & data
    DB-->>Backend: Return saved Lead record
    
    Note over Backend: Trigger non-blocking async calls
    
    par Next.js Event Publication
        Backend->>Kafka: Publish event `lead_ingested` to `nhipdieuxanh-leads`
    and Next.js Blockchain Notarization
        Note over Backend: Only if consent is True
        Backend->>Geth: JSON-RPC eth_sendTransaction (from unlocked wallet)
    end
    
    Backend-->>User: HTTP 200 { success: true, lead }

    Note over AIService: Background Event Loop
    Kafka->>AIService: Consume `lead_ingested` event
    AIService->>DB: Query Lead data & analyze sentiment/persona
    AIService->>DB: UPDATE leads table (write finalized sentiment & persona)
```

---

## 3. RAG Retrieval Flow

This diagram describes how query requests are handled by `@mekong/ask-core`, leveraging SQLite FTS5 for BM25 keyword matching and dense vector similarity scoring with fallback feature hashing.

```mermaid
sequenceDiagram
    autonumber
    actor Client as CRM User / Web UI
    participant Backend as apps/nhipdieuxanh (Next.js)
    participant AskCore as packages/ask-core
    participant SQLite as SQLite (~/.mekong/ask/ask.db)
    participant ModelServer as Remote Model Server / Local Trigrams

    Client->>Backend: POST /api/faq/query (question)
    Note over Backend: Startup require() polyfill intercepts bun:sqlite<br/>and falls back to better-sqlite3 or dummy mock
    
    Backend->>AskCore: AskRetriever.retrieve(query)
    AskCore->>AskCore: sanitizeFtsQuery()
    
    par FTS Sparse Search
        AskCore->>SQLite: Query MATCH fts_index (BM25)
        SQLite-->>AskCore: Return text matching chunks
    and Embeddings Dense Search
        AskCore->>ModelServer: HTTP POST /v1/embeddings (query)
        alt Model Server Successful
            ModelServer-->>AskCore: Return query vector
        else Model Server Offline / Timeout (2000ms)
            Note over AskCore: Fall back to local trigram feature-hashing
            AskCore->>AskCore: Generate hashing embedding
        end
        AskCore->>SQLite: read all chunk vectors
        SQLite-->>AskCore: Return all vector rows
        Note over AskCore: Compute cosine similarity in JS memory<br/>Sort candidates descending
    end

    Note over AskCore: Combine results using Reciprocal Rank Fusion (RRF)<br/>Select top candidates (limit * 3)
    AskCore->>AskCore: AskReranker.rerank() (Heuristic token matching boosts)
    
    Backend-->>Client: Return top chunk context with citations
```

---

## 4. Payment Deposit Webhook Flow

This diagram describes how deposit bookings are processed using MB Bank/SePay HMAC signature-validated webhooks.

```mermaid
sequenceDiagram
    autonumber
    actor Client as Buyer
    participant SePay as SePay Gateway (MB Bank Alert)
    participant Backend as apps/nhipdieuxanh (Next.js)
    participant DB as PostgreSQL

    Client->>SePay: MB Bank Transfer of 10,000,000 VND (Memo: NDX-<leadId>)
    SePay->>Backend: POST /api/payments/sepay (payload & headers)
    
    Note over Backend: Extract headers & signature<br/>Validate HMAC signature with timingSafeCompare
    
    alt Signature Invalild and isProduction is True
        Backend-->>SePay: HTTP 400 Bad Request
    else Signature Verified OR (Bypassed and isProduction is False)
        Note over Backend: Enforce transferType === 'in'<br/>Enforce transferAmount === 10,000,000 VND<br/>Extract leadId from transaction memo
        
        alt Lead already won (Idempotency)
            Backend-->>SePay: HTTP 200 { success: true, message: "already won" }
        else Lead status is pending
            Backend->>DB: Update lead status to 'won'
            DB-->>Backend: Success
            Backend-->>SePay: HTTP 200 { success: true }
        end
    end
```
