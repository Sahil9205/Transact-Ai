# 🏛️ TransactAI — Architecture Flowcharts & Visual System Blueprints

This document contains the complete collection of **10 production architectural flowcharts and system blueprints** for **TransactAI**. Each diagram models a critical subsystem—from multi-host protocol ingestion, sub-85ms vector discovery, and atomic gatekeeping to cryptographic payment settlements and 3-layer audit observability.

---

## 📑 Table of Contents

1. [Universal Autonomous Commerce Gateway Architecture](#1-universal-autonomous-commerce-gateway-architecture)
2. [<85ms Hybrid Semantic Vector Discovery Pipeline](#2-85ms-hybrid-semantic-vector-discovery-pipeline)
3. [Atomic Pre-Flight Gatekeeper & Spending Policy Engine](#3-atomic-pre-flight-gatekeeper--spending-policy-engine)
4. [Two-Stage Multi-Criteria Ranking Pipeline](#4-two-stage-multi-criteria-ranking-pipeline)
5. [Autonomous Commerce State Graph (LangGraph Execution)](#5-autonomous-commerce-state-graph-langgraph-execution)
6. [Razorpay Cryptographic Payment & Webhook Settlement Lifecycle](#6-razorpay-cryptographic-payment--webhook-settlement-lifecycle)
7. [3-Layer Audit Trail & Order Lifecycle Architecture](#7-3-layer-audit-trail--order-lifecycle-architecture)
8. [Multi-Dimensional Constraint Relaxation & Autonomous Recovery](#8-multi-dimensional-constraint-relaxation--autonomous-recovery)
9. [Dual-Mode Protocol Bridge: Local STDIO vs Remote Streamable HTTP](#9-dual-mode-protocol-bridge-local-stdio-vs-remote-streamable-http)
10. [Merchant Onboarding, FastEmbed Vectorization & Payout Pipeline](#10-merchant-onboarding-fastembed-vectorization--payout-pipeline)

---

## 1. Universal Autonomous Commerce Gateway Architecture

### 💡 Purpose & Core Invariants
Connects frontier conversational AI models (Claude, ChatGPT, Gemini) to real-world local merchants and quick-commerce providers without exposing raw databases or proprietary APIs. All external tool calls are normalized into a single canonical `ProductSchema`.

```mermaid
graph TB
    subgraph Hosts["1. Multi-Host AI Ingestion Layer"]
        C1["Claude (Model Context Protocol - stdio / HTTP)"]
        C2["ChatGPT (OpenAPI Actions / Custom GPT)"]
        C3["Google Gemini (Function Calling / Tools)"]
    end

    subgraph Gateway["2. TransactAI Deterministic Gateway Core"]
        MCP["MCP Protocol Router & JSON-RPC Gateway"]
        INTENT["Structured Intent Parser (BuyerIntentSchema)"]
        DISC["FastEmbed Semantic Vector Search (<85ms)"]
        GATE["Atomic Pre-Flight Gatekeeper & Policy Engine"]
        GRAPH["LangGraph Commerce State Machine"]
    end

    subgraph Adapters["3. Canonical Provider Adapters"]
        LA["LocalMerchantAdapter (PostgreSQL + Pincode Radius)"]
        BA["BlinkitAdapter (Dark Store 10-min Delivery)"]
        ZA["ZeptoAdapter (Instant Grocery Quick-Commerce)"]
        SA["SwiggyAdapter (Food & Grocery Marketplace)"]
    end

    subgraph Storage["4. Financial & Storage Settlement Layer"]
        DB[("PostgreSQL on Railway<br/>(Merchants, Orders, Payments, Audit)")]
        VEC[("Qdrant Cloud Vector DB<br/>(384d BGE Embeddings)")]
        RZP["Razorpay Hosted Checkout & Webhooks (HMAC-SHA256)"]
    end

    Hosts --> MCP
    MCP --> INTENT
    INTENT --> DISC
    DISC --> GATE
    GATE --> GRAPH
    GRAPH --> LA & BA & ZA & SA
    LA & BA & ZA & SA --> DB & VEC
    GRAPH --> RZP
```

---

## 2. <85ms Hybrid Semantic Vector Discovery Pipeline

### 💡 Purpose & Core Invariants
In autonomous multi-turn shopping, compound agent latency must stay sub-100ms. By executing local in-memory embeddings via `FastEmbed` (`BAAI/bge-small-en-v1.5`) and parallelizing Qdrant Cloud HNSW vector searches with PostgreSQL relational lookups, TransactAI achieves a **78.05 ms** end-to-end trace. Trimming candidate payloads from 1.15 MB down to 20 KB eliminated state serialization bottlenecks.

```mermaid
graph LR
    subgraph Input["1. Buyer Prompt"]
        P["User Natural Language Prompt:<br/>'1kg Rasgulla under ₹500 in 110001'"]
    end

    subgraph Embed["2. Local FastEmbed Engine"]
        FE["FastEmbed (bge-small-en-v1.5)<br/>384-dim dense vector<br/>⏱️ ~14ms (In-Memory, 0ms Network)"]
    end

    subgraph Search["3. Parallel Fan-Out Discovery"]
        QD[("Qdrant Cloud Cluster<br/>HNSW Cosine Vector Index<br/>⏱️ ~35ms")]
        PG[("PostgreSQL Railway<br/>Pincode & Merchant Filter<br/>⏱️ ~18ms")]
    end

    subgraph Optimization["4. Payload Optimization"]
        TRIM["Candidate Payload Trimmer<br/>Capped to Top 5 items<br/>1.15 MB ➔ 20 KB payload"]
    end

    subgraph Output["5. LangSmith Verified Trace"]
        OUT["Validated Candidates<br/>⚡ Total Latency: ~78.05 ms (< 85 ms Target)"]
    end

    P --> FE
    FE --> QD & PG
    QD & PG --> TRIM
    TRIM --> OUT
```

---

## 3. Atomic Pre-Flight Gatekeeper & Spending Policy Engine

### 💡 Purpose & Core Invariants
Never permit an LLM to initiate payment on unverified inventory or exceed buyer-defined financial caps. The Pre-Flight Gatekeeper combines deterministic product truth verification with spending limit enforcement as an atomic pre-condition.

```mermaid
graph TD
    PROPOSAL["Agent Proposed Product Candidate"] --> GATE["Atomic Gatekeeper Service (app/services/gatekeeper_service.py)"]

    subgraph Verification["Step 1: Authoritative Truth Verification"]
        GATE --> V1["Live DB Price Check (Paise precision)"]
        GATE --> V2["Inventory Stock Check (Qty >= Requested)"]
        GATE --> V3["Freshness Tier Verification (Real-time vs Cached)"]
        GATE --> V4["Fulfillment SLA Validation (Prep time + Delivery)"]
    end

    subgraph Policy["Step 2: Deterministic Spending Limits"]
        GATE --> P1{"Per-Transaction Limit<br/>Amount <= Max Per Tx?"}
        GATE --> P2{"Daily Spending Budget<br/>Spent Today + Amount <= Daily Limit?"}
        GATE --> P3{"Category Whitelist<br/>Category in Allowed Categories?"}
    end

    V1 & V2 & V3 & V4 --> EVAL{"Both Checks Pass?"}
    P1 & P2 & P3 --> EVAL

    EVAL -->|"YES"| ALLOW["✅ Decision: ALLOW<br/>Emit PREFLIGHT_PASSED Audit<br/>Proceed to Human Confirmation"]
    EVAL -->|"NO"| BLOCK["🚫 Decision: BLOCK<br/>Emit POLICY_VIOLATED Audit<br/>Trigger Recovery Engine"]
```

---

## 4. Two-Stage Multi-Criteria Ranking Pipeline

### 💡 Purpose & Core Invariants
Guarantees zero commercial bias. Hard constraints (budget cap, delivery radius, out of stock) immediately disqualify items regardless of rating or provider prominence. Surviving candidates are ranked using a multi-factor weighted scoring algorithm.

```mermaid
graph TD
    ALL["Raw Candidate Pool (Sharma Sweets, Blinkit, Zepto, Swiggy)"] --> STAGE1{"Stage 1: Hard Constraint Filter"}

    STAGE1 -->|"Price > Budget"| DROP1["❌ Excluded (Exceeds Budget)"]
    STAGE1 -->|"Pincode Out of Radius"| DROP2["❌ Excluded (Cannot Deliver)"]
    STAGE1 -->|"Stock = 0"| DROP3["❌ Excluded (Out of Stock)"]

    STAGE1 -->|"Passes All Hard Constraints"| STAGE2["Stage 2: Multi-Factor Weighted Scoring"]

    subgraph Scoring["Deterministic Formula"]
        STAGE2 --> S1["Budget Fit Score (0.35) — Maximum savings"]
        STAGE2 --> S2["Fulfillment Speed (0.30) — Fastest delivery/prep"]
        STAGE2 --> S3["Semantic Match (0.20) — Vector cosine distance"]
        STAGE2 --> S4["Data Freshness (0.15) — Verified live tier"]
    end

    S1 & S2 & S3 & S4 --> RANK["🏆 Ranked Candidates (1st, 2nd, 3rd) Presented to User"]
```

---

## 5. Autonomous Commerce State Graph (LangGraph Execution)

### 💡 Purpose & Core Invariants
Models the complete lifecycle of a transaction as a deterministic, typed state graph with state rollback, conditional branch routing, and a mandatory Human-in-the-Loop (HITL) gate before financial link creation.

```mermaid
graph TD
    START(["User Prompt"]) --> N1["1. parse_intent_node<br/>Extract item, budget, pincode"]
    N1 --> N2["2. multi_provider_discovery_node<br/>Qdrant + DB multi-search"]
    
    N2 --> C1{"Candidates Found?"}
    C1 -->|"No"| N_REC["recovery_recommender_node<br/>Relax constraints across 4 dimensions"]
    C1 -->|"Yes"| N3["3. gatekeeper_verification_node<br/>Live verification & policy checks"]

    N3 --> C2{"Gatekeeper Result"}
    C2 -->|"BLOCK"| N_REC
    C2 -->|"ALLOW"| N4["4. order_proposal_node<br/>Format quote, SLA & savings"]

    N4 --> HITL{{"⏸️ Human-in-the-Loop Gate<br/>User reviews & confirms with Phone"}}
    HITL -->|"Confirmed"| N5["5. razorpay_order_node<br/>Generate secure checkout link"]
    HITL -->|"Rejected / Cancelled"| END(["End Session / Cancelled"])
    N5 --> END
    N_REC --> END
```

---

## 6. Razorpay Cryptographic Payment & Webhook Settlement Lifecycle

### 💡 Purpose & Core Invariants
Financial transactions strictly use currency subunits (paise integers) to avoid floating-point drift. Double verification via client HMAC-SHA256 signature checking and asynchronous server webhooks ensures 100% settlement accuracy with idempotency keys.

```mermaid
sequenceDiagram
    autonumber
    actor Buyer as 🛒 Buyer
    participant Frontend as 🖥️ Hosted Checkout (/pay/{order_id})
    participant Core as ⚙️ TransactAI Server
    participant DB as 🗄️ PostgreSQL (Railway)
    participant RZP as 💳 Razorpay Gateway

    Buyer->>Frontend: Opens hosted payment page
    Frontend->>Core: GET /api/v1/payments/orders/{id}
    Core->>DB: Fetch order (amount: 4000 paise = ₹40.00)
    Core-->>Frontend: Render order summary & Razorpay options

    alt Razorpay Live Checkout
        Buyer->>Frontend: Pays via UPI / Card
        Frontend->>RZP: Process payment
        RZP-->>Frontend: Return razorpay_payment_id & signature
        Frontend->>Core: POST /api/v1/payments/verify-signature
        Note over Core: HMAC-SHA256 Cryptographic Check
        Core->>DB: UPDATE payments SET status='success', transaction_id='pay_...'
        Core->>DB: UPDATE orders SET status='order_created', transaction_id='pay_...'
    else Asynchronous Webhook Settlement
        RZP->>Core: POST /api/v1/payments/webhook (payment.captured)
        Note over Core: Webhook Signature & Idempotency Check
        Core->>DB: Settle payment & order if not already settled
    end

    Core-->>Frontend: Payment Verified ✅
    Frontend-->>Buyer: Show Success + "Track Order in Buyer Console"
```

---

## 7. 3-Layer Audit Trail & Order Lifecycle Architecture

### 💡 Purpose & Core Invariants
Provides full regulatory compliance, fraud prevention, and operational debugging by writing every agent action across three distinct observability tiers while transitioning the order through a strict finite state machine.

```mermaid
graph TD
    ACTION["Agent Commerce Action (Intent / Gatekeeper / Payment / Fulfillment)"] --> ENGINE["3-Layer Production Audit Engine (app/services/audit_service.py)"]

    subgraph Layer1["Layer 1: Immutable DB Ledger"]
        ENGINE --> L1["audit_events Table<br/>(event_type, timestamp, user_id, order_id, amount, reason, metadata)"]
    end

    subgraph Layer2["Layer 2: Structured JSON Logs"]
        ENGINE --> L2["Structlog JSON Logger<br/>(Machine-readable stdout/file for ELK/Datadog)"]
    end

    subgraph Layer3["Layer 3: Distributed Observability"]
        ENGINE --> L3["LangSmith Traces & Run Tags<br/>(Latency profiling, token tracking, eval)"]
    end

    subgraph StateMachine["Complete Order State Machine"]
        S1["discovered"] --> S2["verified"]
        S2 --> S3["user_confirmed"]
        S3 --> S4["payment_pending"]
        S4 --> S5A["payment_success"]
        S4 -.-> S5B["payment_failed"]
        S5A --> S6["order_created"]
        S6 --> S7A["ready_for_pickup / out_for_delivery"]
        S6 -.-> S7B["cancelled"]
        S7A --> S8["completed"]
    end

    ENGINE --> StateMachine
```

---

## 8. Multi-Dimensional Constraint Relaxation & Autonomous Recovery

### 💡 Purpose & Core Invariants
When an exact match fails (e.g. ₹300 budget in 15 mins), the agent never dead-ends. It automatically explores four orthogonal relaxation vectors to propose relevant, actionable alternatives.

```mermaid
graph TD
    FAIL["Exact Criteria Yields 0 Matches<br/>(e.g. 'Rasgulla under ₹300 in 15 mins')"] --> ENG["Autonomous Recovery Engine (app/services/recovery_service.py)"]

    subgraph Four_Dimensions["4-Way Autonomous Constraint Relaxation"]
        ENG --> D1["1. Price Headroom (+10-25%)<br/>'₹300 mein nahi hai, par ₹350 mein Zepto par available hai'"]
        ENG --> D2["2. Timeline / SLA Extension<br/>'15 min mein nahi hai, par 30 min standard delivery mein available hai'"]
        ENG --> D3["3. Cross-Platform Switching<br/>'Sharma Sweets out of stock hai, par Blinkit par in stock hai'"]
        ENG --> D4["4. Category Substitution<br/>'Rasgulla nahi mila, par Gulab Jamun ₹280 mein available hai'"]
    end

    D1 & D2 & D3 & D4 --> RANK["Rank & Tag Alternatives Clearly"]
    RANK --> AGENT["Agent Message to User with Actionable Alternatives"]
```

---

## 9. Dual-Mode Protocol Bridge: Local STDIO vs Remote Streamable HTTP

### 💡 Purpose & Core Invariants
Bridges the architectural gap between local desktop agent processes (Claude Desktop via `stdio` pipes) and remote cloud-native assistants (ChatGPT Actions and Claude.ai Web via HTTPS JSON-RPC 2.0).

```mermaid
graph TB
    subgraph Clients["Heterogeneous AI Clients"]
        LOCAL["Claude Desktop App (Local Laptop)"]
        REMOTE["ChatGPT Custom GPT / Claude.ai Web (Cloud Servers)"]
    end

    subgraph Dual_Mode["Dual-Mode Transport Bridge"]
        STDIO["STDIO Transport Handler<br/>(Reads stdin, writes stdout)"]
        HTTP["Streamable HTTP / JSON-RPC Handler<br/>(POST /mcp & /execute-tool)"]
    end

    subgraph Registry["Unified MCP Commerce Tools Registry"]
        REG["tools.py Registry<br/>• transact_search_catalog<br/>• transact_verify_order_preflight<br/>• transact_create_order_payment<br/>• transact_register_merchant"]
    end

    subgraph Core["Execution Core"]
        SERVICES["PostgreSQL + Qdrant + Razorpay"]
    end

    LOCAL -->|"Process Pipes (stdin/stdout)"| STDIO
    REMOTE -->|"HTTPS JSON-RPC 2.0 / OpenAPI"| HTTP
    STDIO & HTTP --> REG
    REG --> SERVICES
```

---

## 10. Merchant Onboarding, FastEmbed Vectorization & Payout Pipeline

### 💡 Purpose & Core Invariants
Allows non-technical physical merchants to register their store in under 3 minutes. The pipeline automatically persists store coordinates and bank/UPI settlement credentials into PostgreSQL while vectorizing catalog offerings into Qdrant Cloud.

```mermaid
graph LR
    subgraph Wizard["6-Step Merchant Wizard (/merchant/register)"]
        W1["1. Identity & Name"] --> W2["2. Location & Radius"]
        W2 --> W3["3. Owner Contacts"]
        W3 --> W4["4. Catalog & Pricing"]
        W4 --> W5["5. UPI & Bank Details"]
        W5 --> W6["6. Launch Celebration"]
    end

    subgraph Ingestion["Backend Ingestion Pipeline"]
        POST["POST /api/v1/merchants"]
        FE["FastEmbed Engine<br/>Vectorize Product Description"]
    end

    subgraph Storage["Dual-Database Persistence"]
        PG[("PostgreSQL (Railway)<br/>• merchants (Store info + Bank Payouts)<br/>• products (Price, Units, Stock)<br/>• sk_live_... API Keys")]
        QD[("Qdrant Cloud<br/>• 384d Dense Vector Index<br/>• Ready for AI Search in <85ms")]
    end

    W6 --> POST
    POST --> PG
    POST --> FE --> QD
```

---

*Authored for the TransactAI Open Source Project. All diagrams adhere to GitHub native Mermaid syntax.*
