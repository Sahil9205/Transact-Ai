# Transact AI

## Overview

Transact AI is a provider-independent AI Commerce Agent designed for the Razorpay Buildathon. It aims to bridge the gap between intent-driven natural language interpretation (handled by the AI) and secure, deterministic execution (handled by code).

### Architecture Principle: AI Interprets, Deterministic Code Verifies
The core philosophy is that an LLM acts purely as the interpretation layer. The AI determines what the user wants, but all transaction verification, pricing computation, constraint checking, and final API calls to payment gateways are handled by hardcoded, deterministic pathways to prevent hallucinated financial states.

### Architecture Diagram

```text
+---------------------+      Natural Language       +----------------------+
|     User Client     | <=========================> |   FastAPI Endpoint   |
+---------------------+                             +----------------------+
                                                               |
                                                               | (API Routing)
                                                               v
+---------------------+                             +----------------------+
|    Vector Store     | <--- Semantic Search ------ |   LangGraph Agent    |
|      (Qdrant)       |                             |   (Orchestrator)     |
+---------------------+                             +----------------------+
       [Phase N]                                               |
                                                               | (Intent -> Action)
                                                               v
                                                    +----------------------+
                                                    | Deterministic Logic  |
                                                    | (SQLAlchemy DB Ops)  |
                                                    +----------------------+
                                                               |
                                                               | (Payment Intent)
                                                               v
                                                    +----------------------+
                                                    |   Razorpay Gateway   |
                                                    +----------------------+
                                                           [Phase N]
```

## Phase-Based Development

We are building this iteratively:
- **Phase 0:** Project initialization, framework configuration, foundational async setup, database ORM setup.
- **Phase N (Future):** LangGraph integration, Qdrant vector search implementation, and Razorpay integrations.

## Setup Instructions

1. **Environment Setup:** Ensure you have Python 3.12+ (e.g., via Conda).
   ```bash
   conda activate razorpay
   ```

2. **Install Dependencies:**
   Install dependencies and dev packages via pip.
   ```bash
   pip install -e ".[dev]"
   ```

3. **Environment Variables:**
   Copy the example environment file to `.env` and fill in necessary details (for future phases).
   ```bash
   cp .env.example .env
   ```

4. **Run the Server:**
   Start the FastAPI development server.
   ```bash
   uvicorn app.main:app --reload
   ```
   *(Note: The `app/` structure will be introduced in subsequent phases)*

## Running Tests

Run the tests using pytest:
```bash
pytest
```

## Documentation

For a detailed explanation of why specific technologies were chosen (FastAPI, SQLAlchemy, Pydantic, etc.), please read the [Architecture Decisions](docs/architecture_decisions.md).

---
*License: [Placeholder]*
