# Security Policy

## Supported Versions

TransactAI is an evaluation release built for the Razorpay Buildathon and frontier AI commerce orchestration. Security updates are applied to the active `main` branch.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

---

## Architectural Safeguards

TransactAI implements a strict security axiom: **"AI Interprets, Deterministic Code Verifies."**
Probabilistic language models are never permitted to authorize transactions or bypass deterministic software invariants:

1. **Cryptographic Payment Validation**:
   - Razorpay payment return signatures and webhook events are validated using constant-time `hmac.compare_digest` with HMAC-SHA256 (`app/services/payment_service.py`).
2. **Ephemeral Pre-flight Tokens**:
   - Pre-flight order verification issues a cryptographically signed HMAC-SHA256 token binding `user_id`, `product_id`, and `quantity` with a 15-minute TTL to prevent client-side cart tampering between gatekeeper review and payment link generation (`app/services/gatekeeper_service.py`).
3. **Atomic Concurrency Control**:
   - Inventory decrements are executed via conditional SQL operations (`quantity = quantity - :qty WHERE quantity >= :qty`), eliminating race conditions, double-allocations, and overselling under concurrent load (`app/db/repository.py`).
4. **Idempotency Keys**:
   - Payment order creation enforces client-provided idempotency keys to ensure at-most-once transaction initialization and avoid accidental duplicate charges (`app/services/payment_service.py`).
5. **Vendor Authentication & Tenant Isolation**:
   - Merchant authentication utilizes PBKDF2 password hashing (SHA-256 with 100,000 iterations) and RFC 7519 HS256 JWT tokens.
   - All repository database queries strictly isolate vendor records by `merchant_id` (`app/db/repository.py`).
6. **Credential Redaction & Telemetry Hygiene**:
   - Structured logging via `structlog` automatically masks authorization headers, API keys, and sensitive buyer credentials (`app/core/logging.py`).
7. **Test Mode Enforcement**:
   - The platform exclusively integrates with Razorpay Test Mode keys (`rzp_test_*`). No live financial settlements, bank debits, or customer payouts are executed.

---

## Reporting a Vulnerability

We take the security of TransactAI seriously. If you discover a security vulnerability or potential threat:

1. **Do not create a public GitHub issue.**
2. Send an email directly to the project maintainer:
   - **Contact**: Sahil Kumar
   - **Email**: [sahil.kr9205@gmail.com](mailto:sahil.kr9205@gmail.com)
   - **Subject**: `[SECURITY VULNERABILITY] TransactAI - <Brief Description>`
3. Please include:
   - Detailed description of the vulnerability.
   - Steps to reproduce or proof-of-concept payload.
   - Impact assessment (e.g., privilege escalation, policy bypass, data exposure).
   - Affected files and components.

### Response SLA
- **Initial Acknowledgement**: Within 48 hours.
- **Triage & Remediation Plan**: Within 7 business days.
- **Coordinated Disclosure**: Fix released to `main` with attribution in release notes (unless anonymity is requested).
