# 🛍️ Transact AI — Autonomous Multi-Turn Commerce & Payment Engine

[![Build Status](https://img.shields.io/badge/tests-97%20passed-brightgreen.svg)]()
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)]()
[![FastAPI](https://img.shields.io/badge/framework-FastAPI-009688.svg)]()
[![LangGraph](https://img.shields.io/badge/orchestration-LangGraph-FF6F00.svg)]()
[![Qdrant](https://img.shields.io/badge/vector%20db-Qdrant%20Cloud-DC2626.svg)]()
[![Razorpay](https://img.shields.io/badge/payment-Razorpay%20Gateway-0C2340.svg)]()

> **Universal Autonomous Commerce Engine**: Empowers local merchants, quick-commerce dark stores (Blinkit, Zepto), and e-commerce giants (Amazon) to be discovered, verified, and transacted natively from AI assistants (ChatGPT, Gemini, Claude) with zero context switching.

---

## 🏗️ Architectural Principle: *AI Interprets, Deterministic Code Verifies*

Large Language Models (LLMs) act purely as the **natural language interpretation layer**. All critical transaction invariants — **live stock availability, price freshness, daily spending caps, Razorpay HMAC-SHA256 signature verification, and 3-layer audit trails** — are strictly enforced by deterministic, non-hallucinating code guardrails.

```
                    ┌─────────────────────────────────────────────────────────┐
                    │               External AI Hosts / Clients               │
                    │   (Google Gemini, OpenAI ChatGPT, Anthropic Claude)     │
                    └────────────────────────────┬────────────────────────────┘
                                                 │
                                                 ▼
                    ┌─────────────────────────────────────────────────────────┐
                    │            Transact AI Orchestration Core               │
                    │      FastAPI Gateway + LangGraph State Machine          │
                    └───────┬────────────────────┬────────────────────┬───────┘
                            │                    │                    │
                            ▼                    ▼                    ▼
                    ┌───────────────┐    ┌───────────────┐    ┌───────────────┐
                    │ Qdrant Cloud  │    │ Pre-Flight    │    │ Razorpay Test │
                    │ Vector Search │    │ Gatekeeper    │    │ Payment Links │
                    │ (FastEmbed)   │    │ (Stock/Policy)│    │ & Webhooks    │
                    └───────────────┘    └───────────────┘    └───────────────┘
                            │                    │                    │
                            └────────────────────┼────────────────────┘
                                                 │
                                                 ▼
                                ┌─────────────────────────────────┐
                                │   3-Layer Immutable Audit Trail │
                                │   (DB + Structlog + LangSmith)  │
                                └─────────────────────────────────┘
```

---

## ✨ Key Features & Capabilities

1. **Universal Provider Support**: Works identically for local sweet shops (*Sharma Sweets*), quick-commerce nodes (*Blinkit*, *Zepto*), marketplaces (*Amazon*), and pharmacies (*Apollo*).
2. **Hybrid Semantic Discovery & Ranking Engine**: Blends FastEmbed (`BAAI/bge-small-en-v1.5`) dense vector search with multi-factor scoring (Price, Distance, Rating, Freshness, SLA).
3. **Model Context Protocol (MCP) Server**: Standard JSON-RPC 2.0 endpoint (`/api/v1/mcp`) & stdio CLI (`python -m app.mcp.server`).
4. **Natural Language Intent Parsing**: Supports English, Hindi, and Hinglish prompts (e.g. *"Bhai CP mein 1kg Rasgulla under 500"*).
5. **Atomic Pre-Flight Gatekeeper**: Verifies live stock and enforces user per-transaction & daily spending limits before checkout.
6. **Multi-Dimensional Constraint Relaxation**: Never dead-ends — automatically relaxes Price (+10-30%), Timeline (SLA), Platform (Blinkit/Zepto), or Category Substitutes.
7. **Razorpay Payment Gateway**: Generates test-mode checkout orders, payment links, verifies cryptographic `HMAC-SHA256` signatures, and processes webhooks with idempotency.
8. **3-Layer Production Audit Ledger**: Complete compliance trace recorded in SQLite/PostgreSQL `audit_events`, structured JSON logs (`structlog`), and LangSmith spans.
9. **Multi-LLM Host Connectors**: Exports native tool schemas for Google Gemini (`FunctionDeclaration`), OpenAI (`tools`), and Anthropic (`input_schema`).
10. **Interactive CLI & Showcase Script**: Full terminal REPL (`cli.py`) and automated 5-scenario demo runner (`scripts/demo.py`).

---

## 🚀 Quickstart Guide

### 1. Environment Setup
```powershell
# Activate your Python virtual environment
razorpay\Scripts\activate
```

### 2. Configure Environment
```bash
cp .env.example .env
```
*(Optional: add `QDRANT_URL`, `QDRANT_API_KEY`, `LANGSMITH_API_KEY`, `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`)*

### 3. Seed the Multi-Provider Catalog
```powershell
razorpay\python.exe app/db/seed.py
```

### 4. Run Automated 5-Scenario Showcase
```powershell
razorpay\python.exe scripts/demo.py
```

### 5. Launch the Interactive Terminal CLI
```powershell
razorpay\python.exe cli.py
```

### 6. Start the REST API & MCP Server
```powershell
razorpay\python.exe -m uvicorn app.main:app --reload --port 8000
```
- **Swagger Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Global Manifest**: [http://127.0.0.1:8000/manifest.json](http://127.0.0.1:8000/manifest.json)
- **MCP SSE Stream**: [http://127.0.0.1:8000/api/v1/mcp/sse](http://127.0.0.1:8000/api/v1/mcp/sse)

---

## 🧪 Running the Test Suite
Transact AI maintains **100% test coverage** across all 12 architectural phases:
```powershell
razorpay\python.exe -m pytest tests/ -v
```

---

## 📁 Repository Structure
```
├── app/
│   ├── agent/             # LangGraph state machine, nodes, and compiled workflow
│   ├── api/v1/            # REST API routers (merchants, products, mcp, intent, discovery, policies, agent, payments, orders, audit, recovery, hosts)
│   ├── core/              # Config, structured logging, base exceptions
│   ├── db/                # Async SQLAlchemy models, repositories, database engine, seed catalog
│   ├── domain/            # Pydantic schemas, enums, manifest schemas
│   ├── mcp/               # Model Context Protocol JSON-RPC server and commerce tool definitions
│   ├── providers/         # Provider adapter interfaces (Local, Enterprise, Marketplace)
│   └── services/          # Business logic services (Vector, Intent, Discovery, Gatekeeper, Payment, Order, Audit, Recovery, Host)
├── cli.py                 # Interactive terminal commerce CLI
├── scripts/
│   └── demo.py            # Automated 5-scenario capstone showcase
└── tests/
    ├── integration/       # End-to-end API and workflow tests
    └── unit/              # Isolated service and state machine unit tests
```

---

## 📜 License
MIT License. Built for Razorpay Buildathon & Next-Generation Autonomous Commerce.
