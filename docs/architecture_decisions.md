# Architecture Decisions

> **👋 New to the project?** Please read the [Beginner's Developer Guide](developer_guide.md) first!
> **🔄 Looking for our Tech Debt / Upgrade Roadmap?** See the [Prototype vs Production Guide](prototype_vs_production.md).

The initial phase of Transact AI (Phase 0) focuses on establishing a robust, scalable, and provider-independent foundation. This document captures the key architectural decisions made during this phase.

## Architecture Principle: AI Interprets, Deterministic Code Verifies

The foundation of this commerce agent relies on a strict separation of concerns. AI is exceptionally good at understanding intent, extracting parameters from natural language, and adapting to edge cases. However, AI can also hallucinate and is non-deterministic. In a commerce system handling real transactions, non-determinism is unacceptable.

Therefore, our architectural principle dictates that the AI's role is strictly limited to **interpretation and planning**. Once the AI determines what needs to happen (e.g., "User wants to buy item X for amount Y"), the execution is handed over to **deterministic code**. This deterministic layer verifies business rules, checks constraints, computes final pricing securely, and invokes the payment gateways. This ensures commerce safety, strict auditability, and completely prevents LLM hallucinations from causing incorrect financial transactions.

## Provider-Independent Design

To ensure long-term viability and flexibility, the system is designed to be provider-independent. This means we use canonical domain models for our internal logic and implement adapters to bridge the gap between our internal models and the specific API representations of various providers (e.g., LLMs, search engines, payment gateways like Razorpay). If a provider changes or we wish to integrate an alternative, we simply write a new adapter without altering our core commerce or verification logic.

## Why NOT a Full Framework (Django/Ruby on Rails)

We opted out of using heavy monolithic frameworks like Django because:
1. **No Admin/Template Needs**: We are building a lean, backend-only API layer to serve as an agent orchestration hub. There is no need for HTML templating engines or built-in admin panels.
2. **Async First**: Agentic workflows, multiple LLM provider calls, and asynchronous payment verifications require high concurrency. While frameworks like Django have introduced async support, they are primarily synchronous at their core, which can lead to friction when building entirely async systems.
3. **Decoupling**: We want complete control over how our data flows and how models are structured without being bound to a specific ORM's migration patterns deeply intertwined with the framework.

---

## Detailed Technology Choices

### 1. Web Framework: FastAPI
We chose **FastAPI** over Flask, Django, or a plain REST implementation for the following reasons:
- **Async-First**: Native support for Python's `asyncio`, crucial for non-blocking I/O when making concurrent API calls to LLMs and payment gateways.
- **Pydantic Integration**: Deeply integrated with Pydantic for request/response validation.
- **Automatic Documentation**: Out-of-the-box Swagger UI and ReDoc (OpenAPI) generation, accelerating frontend and agent integration.
- **Dependency Injection**: Robust dependency injection system simplifies testing and managing state (e.g., database sessions).

### 2. Database & ORM: SQLAlchemy 2.0 (Async) + SQLite
- **Why SQLAlchemy 2.0 Async** (over raw SQL, Django ORM, or Tortoise): It is the Python standard for ORMs, highly mature, and its 2.0 version offers first-class support for `asyncio` while maintaining strict static typing.
- **Provider-Agnostic**: It allows us to seamlessly swap out the underlying database engine without changing our query logic.
- **Why SQLite for prototype** (over PostgreSQL day 1): SQLite requires zero configuration or external daemon management, providing the fastest iteration loop for the buildathon phase. Because we use SQLAlchemy, migrating to PostgreSQL in later phases is a matter of changing the connection string and installing the async pg driver.

### 3. Data Validation: Pydantic v2 & pydantic-settings
- **Why Pydantic v2** (over dataclasses, attrs, marshmallow): Pydantic is native to FastAPI and handles complex data validation intrinsically. Version 2 is rewritten in Rust, providing immense performance benefits. It also seamlessly generates JSON Schemas, which is vital when describing our tools/functions to the LLM.
- **Why pydantic-settings** (over python-dotenv alone or dynaconf): It provides strictly typed environment configurations. It validates environment variables at startup, preventing runtime errors due to missing or misconfigured settings. It integrates naturally with `.env` files.

### 4. Logging: structlog
- **Why structlog** (over stdlib logging or loguru): For an agentic system and commerce platform, simple text logs are insufficient. We need **structured JSON output** to trace AI decisions, agent routing, and transaction states. `structlog` offers a production-grade processor pipeline and allows context binding (e.g., binding a `transaction_id` to all subsequent log entries in a request flow).

### 5. Testing: pytest + pytest-asyncio
- **Why pytest** (over unittest): It provides a vastly superior developer experience with its powerful fixture system, parameterization, and plugin ecosystem.
- **Async Support**: `pytest-asyncio` allows us to effortlessly test our async endpoints and database operations natively.

---

## Future Phases Technology Stack

While Phase 0 focuses on the foundation, later phases will incorporate the following:

### 1. Agent Orchestration: LangGraph
- **Why LangGraph** (over raw LangChain, CrewAI, AutoGen): Instead of relying on implicit loops or unpredictable auto-routing, LangGraph enforces an **explicit state machine**. We define typed states and deterministic routing paths. This means failure paths, human-in-the-loop interventions, and fallbacks are first-class citizens—a non-negotiable requirement for financial transactions.

### 2. Vector Search: Qdrant
- **Why Qdrant** (over Pinecone, Weaviate, ChromaDB): Qdrant is open-source and can be easily self-hosted or run locally via Docker (fast local dev), but also scales to managed cloud. It offers typed payload filtering, allowing us to perform hybrid searches (e.g., vector similarity + strict metadata filtering for price ranges or stock availability).

### 3. Payment Gateway: Razorpay
- **Why Razorpay**: It is a buildathon requirement, but inherently, Razorpay provides the robust APIs required for Indian payments, comprehensive webhook support for asynchronous state updates, and a dedicated test mode for safe development of the commerce layer.

---

## Dependency Summary

| Dependency | Category | Purpose | Why this over alternatives? |
| :--- | :--- | :--- | :--- |
| `fastapi` | Core | Web Framework | Native async, incredible speed, Pydantic integration |
| `uvicorn` | Core | ASGI Server | Standard, fast async server for FastAPI |
| `sqlalchemy` | Core | ORM | Industry standard, robust 2.0 async support |
| `aiosqlite` | Core | Async DB Driver | Non-blocking database ops for SQLite prototyping |
| `pydantic` | Core | Data Validation | Built into FastAPI, strict types, fast (Rust) |
| `pydantic-settings`| Core | Config Management | Type-safe environment variable parsing |
| `structlog` | Core | Logging | Structured JSON logging with context binding |
| `python-dotenv` | Core | Env Loader | Standard, simple integration for local secrets |
| `httpx` | Core / Dev | HTTP Client | Async-first, non-blocking requests |
| `pytest` | Dev | Testing | Powerful fixtures, less boilerplate than unittest |
| `pytest-asyncio` | Dev | Async Tests | Effortless testing for async endpoints |
| `ruff` | Dev | Linter/Formatter | 10-100x faster than flake8/black (Rust-based) |
| `mypy` | Dev | Type Checker | Standard static type verification |
| `langgraph` | Future | Orchestration | Explicit state machine over unpredictable auto-routing |
| `langchain-core` | Future | LLM Abstraction | Prevents vendor lock-in for AI models |
| `qdrant-client` | Future | Vector DB | Typed payload filtering, local/cloud flexibility |
| `razorpay` | Future | Payments | Official robust SDK for financial transactions |
| `google-genai` / `openai`| Future | LLM Provider | Required intelligence for the agentic layer |
