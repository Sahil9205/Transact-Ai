# 🔄 Transact AI: Prototype vs Production Architecture

This document serves as an **Antigravity Context & Architecture Evolution Roadmap**. It explicitly defines what trade-offs and implementations we are using **NOW (Prototype/Buildathon phase)** vs what we will replace them with in **FUTURE (Production Scale)**.

This ensures all developers and AI agents working on this codebase understand current design boundaries and the future migration path.

---

## 🗺️ Quick Transition Matrix

| Component | 🛠️ Current (Prototype / Now) | 🚀 Future (Production / Later) | Why the trade-off was made |
| :--- | :--- | :--- | :--- |
| **DB Migrations** | `Base.metadata.create_all()` | **Alembic Migrations** | Rapid schema prototyping without creating migration files on every tweak. |
| **Database Engine** | **SQLite** (`sqlite+aiosqlite`) | **PostgreSQL** (`postgresql+asyncpg`) | Zero setup, local file database for quick iteration; easily switched via SQLAlchemy connection string. |
| **Primary Keys & IDs** | Auto-increment `int` (DB) + `UUID4` (Public) | Auto-increment `int` (DB) + **UUIDv7 / Nanoid** (Public) | Time-sortable UUIDs (UUIDv7) improve B-tree index performance at scale. |
| **Currency Support** | Stored `currency="INR"` (default) | **Multi-currency engine with real-time FX** | Avoids hardcoding while keeping calculations simple in paise (₹). |
| **Provider Adapters** | Local DB Adapter + Mock Quick-Commerce (Blinkit/Zepto simulated) | **Real Partner APIs (REST/GraphQL/Webhooks)** with OAuth, Circuit Breakers & Rate Limiters | Quick-commerce platforms do not have public open sandbox APIs. |
| **Vector Database** | **Qdrant Cloud** (production cluster from day 1) | Scale horizontally, add hybrid dense+sparse search | No prototype shortcuts — semantic search is core to our agent's discovery. |
| **Payment Gateway** | **Razorpay Test Mode** (`rzp_test_...`) | **Razorpay Live Mode** + Delegated Agent Auth (ACP / Tokenized Mandates) | Safe testing of payment flows, signatures, and mock webhooks. |
| **User Authorization** | Application-level spending policy checks | **Bank-grade Delegated Token Authorization** (RBI e-mandate / UPI AutoPay) | Prototype verifies safety without handling banking secrets or PINs. |
| **Order Notifications** | Mock/In-App structured logs | **Twilio / WhatsApp Business API / Push Notifications** | Keeps the prototype self-contained without third-party messaging costs. |
| **Agent Orchestration** | **LangGraph + LangSmith Tracing & Evals** (production-grade from day 1) | Scale with LangGraph Cloud, add A/B eval pipelines | Observability, replayability, and latency monitoring are not optional — they're built-in. |
| **Audit Trail** | **Production-grade**: structlog + DB `audit_events` + LangSmith traces | Add Grafana dashboards, alerting, long-term archival | Every transaction, every decision, every failure — logged permanently. Audit is NEVER a prototype shortcut. |
| **Merchant Portal & Auth** | **Self-serve clean light web portal** (`/merchant/register`, `/merchant/dashboard`) + API Key auth (`sk_live_...`) | **Decoupled Next.js / React SPA** with OAuth 2.0, GST/KYC auto-verification via Sandbox API | Zero-setup single-service hosting on Railway; allows merchants to go live immediately while keeping production roadmap clear. |
| **Catalog Ingestion** | Instant web modal / REST / MCP tool with immediate Qdrant Cloud vector sync | **Bulk CSV/Excel Ingestion Queue** (Celery/Temporal) + ONDC Beckn protocol sync | Prototype allows atomic, verifiable product publishing; bulk ingestion needed at 10,000+ SKU scale. |

---

## 🔍 Detailed Component Deep-Dive

### 1. Database Schema Management
* **Now (Prototype):** 
  * We use SQLAlchemy's `await db_manager.init_db()` which calls `Base.metadata.create_all()`.
  * If a model changes, we simply delete `data/commerce.db` or let SQLite create new tables on startup.
* **Later (Production):** 
  * Introduce **Alembic** (`alembic init alembic`).
  * Every schema change produces an auto-generated versioned migration script (`alembic revision --autogenerate -m "add_column"`).
  * Run migrations during CI/CD before container startup (`alembic upgrade head`).

### 2. Database Engine & Persistence
* **Now (Prototype):** 
  * `sqlite+aiosqlite:///./data/commerce.db`. Single local file, no background services required.
* **Later (Production):** 
  * `postgresql+asyncpg://user:pass@host:5432/transact_ai` (e.g., Supabase, RDS, Neon).
  * Connection pooling, read replicas, and JSONB indexing for audit events and unstructured manifests.

### 3. Identity and Object References (IDs)
* **Now (Prototype):**
  * Internal: Standard Integer Primary Keys (`id: Mapped[int]`).
  * External: Random UUID4 string (`merchant_id = "mer_..."`, `order_id = "ord_..."`).
* **Later (Production):**
  * Migrate external IDs to **UUIDv7** (time-ordered) or cryptographic Nanoids to prevent fragmentation in large B-tree indexes while maintaining unguessable public IDs.

### 4. Merchant Onboarding & Enterprise Providers
* **Now (Prototype):**
  * **Self-Serve Clean Web Portal:** Merchants can register at `/merchant/register`, receive a secret API key (`sk_live_...`), access their store dashboard at `/merchant/dashboard/{id}`, view incoming orders, and publish new products with immediate Qdrant Cloud vector sync.
  * **AI Agent Onboarding Tool:** External AI hosts can onboard new local shops conversationally using the `transact_register_merchant` MCP tool.
  * **Local Merchants & Enterprise:** Local merchants onboarded directly into our relational database (e.g., *Sharma Sweets*, *Apollo Pharmacy*); simulated quick-commerce hubs (Blinkit / Zepto / Swiggy) returning realistic catalog structures.
* **Later (Production):**
  * **Decoupled React / Next.js Portal:** Multi-tenant dashboard with role-based access control (RBAC), multi-user store management, and real-time WebSocket order notifications.
  * **Automated KYC & Verification:** Real-time GSTIN and PAN validation via government sandbox APIs, automated FSSAI license checks for food merchants.
  * **ONDC & Direct Partner APIs:** Direct ONDC Beckn protocol integration, partner merchant webhooks, and circuit-breaker protected catalog sync.


### 5. Semantic Search & Embeddings
* **From Day 1 (Production-Grade):**
  * **Qdrant Cloud** as our vector database — no local/in-memory shortcuts.
  * Product embeddings generated via FastEmbed or text-embedding models, stored with typed payloads (price, category, pincode, availability).
  * Semantic search powers the agent's discovery: "rasgulla" matches "Bengali sweet, round, syrup-soaked" even without exact keyword match.
* **Future Scale:**
  * Hybrid dense + sparse search for precision + recall balance.
  * Quantized vectors for cost optimization at scale.
  * Multi-tenancy support across providers.

### 6. Payment & Authorization Security
* **Now (Prototype):**
  * Razorpay Test Mode keys for creating mock orders and verifying webhook callbacks.
  * Application-level spending policies (`max_per_transaction`, `daily_limit`).
* **Later (Production):**
  * Tokenized delegated payment authorization (Agentic Payment Protocol / UPI Autopay / e-Mandates).
  * Multi-signature policy evaluation (Hardware Security Module / KMS-secured transaction signing).
  * Webhook replay protection and idempotent payment ledgers.

---

### 7. Agent Orchestration & Observability
* **From Day 1 (Production-Grade):**
  * **LangGraph** for explicit state machine orchestration — typed state, deterministic routing, failure paths as first-class nodes.
  * **LangSmith** tracing on every agent run — full visibility into LLM calls, tool invocations, latencies, and token usage.
  * **LangSmith Evals** to measure agent quality: does it find the right product? Does it respect budget? Does it explain failures clearly?
* **Future Scale:**
  * LangGraph Cloud for managed, scalable deployment.
  * A/B eval pipelines comparing prompt strategies.
  * Custom eval datasets from real user conversations.

### 8. Audit Trail (Permanent, Non-Negotiable)
* **From Day 1 (Production-Grade):**
  * Every significant action is logged to `audit_events` table via `AuditRepository.log_event()` with full context (user, provider, product, amount, reason, result, metadata).
  * `structlog` JSON logging on every operation for searchable structured logs.
  * LangSmith traces capture the AI decision chain alongside the deterministic verification chain.
  * **Three layers of audit**: DB records (queryable) + structured logs (searchable) + LangSmith traces (replayable).
* **Future Scale:**
  * Grafana/Loki dashboards for real-time monitoring.
  * Alert pipelines for anomalies (sudden price spikes, repeated payment failures).
  * Long-term archival to cold storage with retention policies.

> [!IMPORTANT]
> **Audit is NEVER a prototype shortcut.** If a transaction happened, it's logged. If a payment was blocked, the reason is recorded. If the AI made a recommendation, the evidence is traceable. No exceptions.

---

## 🎯 Guiding Rule for AI & Engineers

> **"Write prototype code with production boundaries."**
> 
> Keep layers decoupled through interfaces (e.g., `BaseProviderAdapter`, `PaymentProvider`, `DatabaseManager`). When it's time to replace a prototype component (like swapping SQLite for Postgres, or `create_all` for Alembic), it should require changing **configuration or adapters**, never rewriting core commerce logic!
