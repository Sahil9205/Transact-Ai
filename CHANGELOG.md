# Changelog

All notable changes to the **TransactAI** project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-09-22

### Added
- **Multi-Host Frontier AI Connectors**:
  - Model Context Protocol (MCP) JSON-RPC 2.0 stdio and SSE server (`app/mcp/`) exposing 7 specialized commerce tools.
  - ChatGPT Custom GPT Actions OpenAPI schema (`app/api/v1/manifests.py` and `/.well-known/ai-plugin.json`).
  - Google Gemini Function Calling declarations and Python client guide (`app/api/v1/hosts.py`, `docs/gemini_plugin_guide.md`).
- **Deterministic Commerce Gatekeeper & Pre-flight Validation**:
  - Ephemeral HMAC-SHA256 preflight verification token binding user ID, product ID, and quantity with 15-minute TTL (`app/services/gatekeeper_service.py`).
  - Strict policy rule verification for budget ceilings, delivery pincode coverage, and stock freshness.
- **Settlement & Payment Engine**:
  - Cryptographic Razorpay HMAC-SHA256 signature verification for payment return callbacks and webhooks (`app/services/payment_service.py`).
  - Concurrency-safe atomic inventory decrements (`quantity = quantity - :qty WHERE quantity >= :qty`) preventing race conditions during flash checkouts.
  - Client idempotency key support on order initialization preventing accidental duplicate transactions.
- **Inventory Staleness Guardrail & Merchant Pulse**:
  - Automated 6-hour inventory staleness classification and interactive merchant verification ping flow (`app/services/stock_ping_service.py`).
  - Merchant catalog editing, in-stock/out-of-stock toggles, and live inventory refresh.
- **Merchant Authentication & Store Isolation**:
  - RFC 7519 HS256 JWT vendor authentication with PBKDF2 password hashing (`app/services/auth_service.py`).
  - Multi-tenant database query isolation strictly partitioning vendor inventory and orders (`app/db/repository.py`).
- **Cloud-Native Observability & Health Probes**:
  - Dedicated Kubernetes / Railway `/healthz` (liveness) and `/readyz` (readiness) probe endpoints.
  - Structured logging with automatic PII and authorization credential redaction (`app/core/logging.py`).
- **Automated CI/CD**:
  - GitHub Actions continuous integration workflow running Ruff linting, Mypy static analysis, Pytest with coverage >= 80%, and Next.js 14 production builds (`.github/workflows/ci.yml`).
- **Comprehensive Benchmarks & Verification Suite**:
  - Empirical latency measurement harness (`scripts/bench_discovery.py`) recording reproducible p50/p95/p99 timing data.
  - 96 unit tests and 29 end-to-end integration tests with 82% coverage across all commerce invariants.

### Changed
- Refactored frontend navigation and merchant catalog table to full-width responsive layout with zero horizontal overflow.
- Clarified evaluation trade-offs and added persistent Razorpay test-mode disclosure banners across the application.
- Standardized tool names across MCP, ChatGPT OpenAPI schemas, and documentation.

### Security
- Added root `SECURITY.md` defining supported versions, architectural defense-in-depth principles, and responsible disclosure SLAs.
- Licensed under Business Source License 1.1 (BUSL-1.1), converting automatically to the MIT License on January 1, 2030.
