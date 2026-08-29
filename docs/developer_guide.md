# 🚀 Transact AI: Beginner's Developer Guide

Welcome to the **Transact AI** project! If you're new to backend development, Python, or AI engineering, you are in the right place. This document is designed specifically for beginners (even if you're a first-year CS student) to understand exactly how our project is built, what tools we use, and why we chose them.

Transact AI is a **provider-independent AI Commerce Agent** built for the Razorpay Buildathon. It acts as a smart bridge between a user chatting naturally and strict payment systems.

---

## 🏗️ Project Architecture Overview

### 1. Folder Structure
Here is a simplified view of how our code is organized:

```text
Razorpay/
│
├── docs/                   # Documentation (you are here!)
├── app/                    # All our application code lives here
│   ├── api/                # API endpoints (the doors to our app)
│   │   └── health.py       # Health check endpoints
│   ├── core/               # Configuration, logging, exceptions
│   │   ├── config.py       # App settings (pydantic-settings)
│   │   ├── logging.py      # Structured logging setup
│   │   ├── exceptions.py   # Custom error hierarchy
│   │   └── security.py     # Secret redaction helpers
│   ├── db/                 # Database setup
│   │   └── database.py     # Async SQLAlchemy engine + sessions
│   └── main.py             # FastAPI app entrypoint
│
├── tests/                  # Automated tests to ensure our code works
│   ├── conftest.py         # Shared test fixtures
│   └── unit/               # Unit tests
├── razorpay/               # Conda virtual environment (gitignored!)
├── pyproject.toml          # Project metadata and dependencies list
├── .env.example            # Template for environment variables
└── .env                    # Your local secrets (NOT committed to git)
```

### 2. How Data Flows Through the System
1. **User Request**: A user sends a chat message (e.g., "I want to buy a black t-shirt") to our API.
2. **AI Interpretation**: The AI agent reads the message and identifies the user's intent.
3. **Tool Execution**: The AI agent calls a specific internal function (a "tool") to search the database or prepare an order.
4. **Deterministic Verification**: Normal, strict Python code checks if the item is in stock, calculates the exact price, and prepares the Razorpay link.
5. **Response**: The API sends the payment link and a friendly message back to the user.

### 3. The "AI Interprets, Code Verifies" Principle
AI models are amazing at understanding human language, but they are basically really smart autocorrects—they can sometimes make things up (hallucinate) or make math mistakes. 

In a commerce app dealing with real money, mistakes are unacceptable. Therefore, our golden rule is: **AI Interprets, Deterministic Code Verifies.** 
- The **AI** is only allowed to figure out *what* the user wants (Interpretation).
- Normal **Python code** is responsible for calculating prices, checking inventory, and initiating the payment (Verification). The AI never touches the actual financial transaction!

---

## 💻 How to Set Up the Project

This guide assumes you are on Windows and using **Conda** for virtual environments.

### Step 1: Clone and Create the Environment
```bash
# 1. Clone the repository
git clone https://github.com/Sahil9205/Transact-Ai.git
cd Transact-Ai

# 2. Create a virtual environment inside the project folder
# This keeps all our project's packages isolated from your global system.
conda create --prefix ./razorpay python=3.12 -y

# 3. Activate the environment
conda activate ./razorpay
```

### Step 2: Install Dependencies
We install our project in "editable" mode:
```bash
pip install -e .[dev]
```
*(See the "Gotchas" section to understand what `-e` means!)*

### Step 3: Run the Server
```bash
# Make sure you are in the project root directory
uvicorn app.main:app --reload
```
You can now visit `http://127.0.0.1:8000/docs` in your browser to see our interactive API documentation!

### Step 4: Run the Tests
```bash
pytest
```

### How to Add a New Dependency
If you need a new package (e.g., `requests`), do **not** just run `pip install requests`. 
1. Open `pyproject.toml`.
2. Add the package to the `dependencies` list.
3. Run `pip install -e .[dev]` again to install it.

---

## 📦 Dependency Deep Dive

Here is every single package we use, explained simply.

### Core Dependencies

#### 1. `fastapi>=0.115.0`
- **What it is**: A modern, extremely fast web framework for building APIs with Python.
- **Why we use it**: It helps us create the web server that receives user messages.
- **Why this over alternatives (Flask/Django)**: FastAPI is natively asynchronous (great for waiting on AI responses), automatically generates API documentation, and is much faster than Flask.
- **Where it's used**: [main.py](file:///c:/Users/ASUS/Desktop/resume%20project/Razorpay/app/main.py), [app/api/](file:///c:/Users/ASUS/Desktop/resume%20project/Razorpay/app/api/)
- **Example**:
  ```python
  from fastapi import FastAPI
  app = FastAPI()

  @app.get("/ping")
  def health_check():
      return {"status": "ok"}
  ```

#### 2. `uvicorn[standard]>=0.30.0`
- **What it is**: An ASGI (Asynchronous Server Gateway Interface) web server.
- **Why we use it**: FastAPI is a framework, but it needs a server to actually listen to web traffic and translate it for Python. Uvicorn is that server.
- **Why this over alternatives (Gunicorn)**: Uvicorn is the lightning-fast standard for async Python apps.
- **Where it's used**: Command line (when you run `uvicorn`) or in [main.py](file:///c:/Users/ASUS/Desktop/resume%20project/Razorpay/app/main.py).
- **Example**:
  ```python
  import uvicorn
  if __name__ == "__main__":
      uvicorn.run("transact_ai.main:app", host="0.0.0.1", port=8000)
  ```

#### 3. `sqlalchemy[asyncio]>=2.0.30`
- **What it is**: An Object-Relational Mapper (ORM). It lets you write Python code to interact with databases instead of writing raw SQL strings.
- **Why we use it**: To securely store products, orders, and user data.
- **Why this over alternatives (Django ORM, raw SQL)**: It's the industry standard in Python, incredibly robust, and the new 2.0 version has perfect async support.
- **Where it's used**: [app/db/](file:///c:/Users/ASUS/Desktop/resume%20project/Razorpay/app/db/)
- **Example**:
  ```python
  from sqlalchemy.orm import Mapped, mapped_column
  class User(Base):
      __tablename__ = "users"
      id: Mapped[int] = mapped_column(primary_key=True)
      name: Mapped[str]
  ```

#### 4. `aiosqlite>=0.20.0`
- **What it is**: A library that lets Python talk to SQLite databases asynchronously.
- **Why we use it**: SQLite is a simple database stored in a single file. `aiosqlite` ensures our fast API doesn't freeze up while waiting for the database to save a file.
- **Why this over alternatives (psycopg2)**: We use this because SQLite is great for quick development. Later, we can easily swap to PostgreSQL.
- **Where it's used**: Referenced in our SQLAlchemy connection string in [config.py](file:///c:/Users/ASUS/Desktop/resume%20project/Razorpay/app/core/config.py).

#### 5. `pydantic>=2.7.0`
- **What it is**: A data validation library using Python type hints.
- **Why we use it**: To ensure the data coming into our API (or from the AI) is exactly the shape we expect (e.g., an age is a number, an email is valid). If it's wrong, Pydantic throws a clear error.
- **Why this over alternatives (marshmallow)**: It is insanely fast (written in Rust) and built directly into FastAPI.
- **Where it's used**: Everywhere! API response models in [health.py](file:///c:/Users/ASUS/Desktop/resume%20project/Razorpay/app/api/health.py), domain models in future phases.
- **Example**:
  ```python
  from pydantic import BaseModel
  class Product(BaseModel):
      name: str
      price: float
  ```

#### 6. `pydantic-settings>=2.3.0`
- **What it is**: An extension of Pydantic specifically for managing environment variables (configurations, API keys).
- **Why we use it**: To ensure our app crashes immediately *on startup* if we forget to provide a required API key, rather than crashing later when a user tries to pay.
- **Why this over alternatives (os.getenv)**: Provides type safety (ensures a PORT is an integer) and auto-reads from `.env` files.
- **Where it's used**: [config.py](file:///c:/Users/ASUS/Desktop/resume%20project/Razorpay/app/core/config.py)
- **Example**:
  ```python
  from pydantic_settings import BaseSettings
  class Settings(BaseSettings):
      api_key: str
      database_url: str = "sqlite+aiosqlite:///app.db"
  ```

#### 7. `structlog>=24.1.0`
- **What it is**: A structured logging library.
- **Why we use it**: Instead of printing text logs (`"User 123 bought shirt"`), structlog prints JSON (`{"event": "purchase", "user_id": 123, "item": "shirt"}`). This makes it infinitely easier to search and filter logs in the future.
- **Why this over alternatives (standard logging, loguru)**: Standard logging is clunky for JSON. Structlog is extremely powerful for "context variables" (like attaching a Request ID to every log in a flow).
- **Where it's used**: [logging.py](file:///c:/Users/ASUS/Desktop/resume%20project/Razorpay/app/core/logging.py) and everywhere we log.
- **Example**:
  ```python
  import structlog
  logger = structlog.get_logger()
  logger.info("payment_success", amount=500, currency="INR")
  ```

#### 8. `python-dotenv>=1.0.0`
- **What it is**: A library that reads key-value pairs from a `.env` file and adds them to environment variables.
- **Why we use it**: It securely loads our secrets (like Razorpay keys) without us having to type them into our terminal every time.
- **Why this over alternatives**: It's the standard, simple way to do this in Python.
- **Where it's used**: Used under the hood by `pydantic-settings`.

#### 9. `httpx>=0.27.0`
- **What it is**: A fully featured HTTP client for Python.
- **Why we use it**: Our app needs to talk to other apps over the internet (like the Razorpay API or LLM APIs).
- **Why this over alternatives (requests)**: The famous `requests` library is synchronous. `httpx` is async-first, meaning it doesn't block our server while waiting for an external API response.
- **Where it's used**: Will be used in provider adapters and payment service.
- **Example**:
  ```python
  import httpx
  async with httpx.AsyncClient() as client:
      response = await client.get("https://api.razorpay.com/...")
  ```

#### 10. `qdrant-client>=1.9.0`
- **What it is**: The official Python client for Qdrant Vector Database.
- **Why we use it**: It connects our app to Qdrant Cloud to store product vectors and perform fast semantic search with metadata filters (price, stock, pincode).
- **Why this over alternatives (Pinecone, ChromaDB)**: Qdrant offers rich payload filtering (e.g., semantic match + price <= ₹500 filter) and native async support.
- **Where it's used**: `app/services/vector_service.py`
- **Example**:
  ```python
  from qdrant_client import QdrantClient
  client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
  ```

#### 11. `fastembed>=0.3.0`
- **What it is**: A fast, lightweight library for generating text embeddings locally on CPU using ONNX Runtime.
- **Why we use it**: Converts product names and user queries into dense mathematical vectors (using `BAAI/bge-small-en-v1.5`) without requiring paid external embedding API calls.
- **Why this over alternatives (sentence-transformers, OpenAI API)**: 10x lighter than PyTorch, fast CPU inference, zero cost, completely local.
- **Where it's used**: `app/services/vector_service.py`
- **Example**:
  ```python
  from fastembed import TextEmbedding
  embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
  vectors = list(embedding_model.embed(["Sharma Sweets Rasgulla"]))
  ```

---

### Dev Dependencies (Only used while coding/testing)

#### 12. `pytest`
- **What it is**: A framework that makes it easy to write small tests.
- **Why we use it**: To write automated tests ensuring our commerce logic never breaks when we add new features.
- **Why this over alternatives (unittest)**: `unittest` requires lots of boilerplate code. `pytest` is clean, simple, and powerful.

#### 13. `pytest-asyncio`
- **What it is**: A plugin for `pytest` that allows us to test asynchronous functions natively.
- **Why we use it**: Because FastAPI and our database are async, our tests must be async too.

#### 14. `httpx` (Dev mode)
- **What it is**: The same HTTP client mentioned above.
- **Why we use it here**: FastAPI uses `httpx` internally as a "Test Client" to simulate HTTP requests to our app during tests without actually starting the server.

#### 15. `ruff`
- **What it is**: An extremely fast Python linter and code formatter written in Rust.
- **Why we use it**: It automatically catches mistakes in our code (like unused variables) and formats our code to look clean and consistent.
- **Why this over alternatives (flake8, black, isort)**: Ruff replaces all three of those tools combined and is 10-100x faster.

#### 16. `mypy`
- **What it is**: A static type checker for Python.
- **Why we use it**: Python usually lets you put any type of data in a variable. `mypy` checks our type hints (`def add(a: int, b: int)`) and warns us if we try to pass a string instead of an int, preventing bugs *before* we run the code.

---

### Future Dependencies (Coming Soon 🚀)

#### 17. `langgraph`
- **What it is**: A library for building stateful, multi-actor applications with LLMs.
- **Why we will use it**: Instead of a simple AI chatbot, we need a reliable state machine. LangGraph explicitly routes the AI through different states (e.g., "gathering info" -> "confirming order"), allowing for strict control and fallbacks if the AI gets confused.

#### 18. `langchain-core`
- **What it is**: The base abstractions for LangChain.
- **Why we will use it**: It provides a unified interface. By writing our code using LangChain's abstractions, we avoid "vendor lock-in" and can easily switch between OpenAI, Gemini, or local models.

#### 19. `razorpay`
- **What it is**: The official Python SDK for the Razorpay payment gateway.
- **Why we will use it**: To securely generate payment links, process payments, and verify webhooks. This is the financial engine of our app.

#### 19. `google-generativeai` or `openai`
- **What it is**: The official SDKs for interacting with major LLM providers (Gemini or ChatGPT).
- **Why we will use it**: These will power the "brain" of our commerce agent, allowing it to understand natural language inputs.

---

## 🛠️ Coding Conventions

To keep our codebase clean and professional, we follow these strict rules:

1. **`from __future__ import annotations`**: Put this at the very top of every single Python file. It makes type hinting cleaner and prevents circular import errors with typing.
2. **Type Hints Everywhere**: Every function must declare what types of arguments it takes and what it returns. `def get_user(user_id: int) -> User:`
3. **Async by Default**: Unless it is a purely mathematical/synchronous helper, use `async def` for functions.
4. **Structured Exceptions**: We do not just raise generic exceptions. We raise specific errors with error codes (e.g., `raise PaymentVerificationError(code="PAY_01")`) so the frontend knows exactly what went wrong.
5. **Pydantic Data Contracts**: Whenever data moves from one part of the system to another (API -> Agent, Agent -> Tool), it must be passed inside a Pydantic model, not raw dictionaries.

---

## ⚠️ Common Gotchas for Beginners

### 1. Why is the conda env folder (`razorpay/`) ignored by Git?
Virtual environments contain thousands of files for installed packages, and these are specific to your operating system. We NEVER commit installed dependencies to GitHub. Instead, we commit `pyproject.toml`, and everyone builds their own environment locally.

### 2. Difference between `pip install .` and `pip install -e .`
- `pip install .` takes a snapshot of your code and installs it in the environment. If you edit your code, the changes won't show up until you reinstall.
- `pip install -e .` (editable mode) creates a *shortcut* in the environment pointing directly to your code folders. When you edit code and hit save, the server updates instantly!

### 3. What does `_env_file=None` mean in tests?
In `config.py`, we often set `_env_file=None` for testing configurations. This ensures our tests don't accidentally load our real production `.env` file containing real API keys or production database URLs. We want tests to run in a purely isolated environment.

### 4. What does `asyncio_mode = "auto"` mean?
In our `pytest.ini`, this setting tells the pytest-asyncio plugin to automatically treat any `async def` test as an async test without us having to write `@pytest.mark.asyncio` above every single test function. It saves time and boilerplate!

---
*Happy Coding! The AI Commerce revolution starts here.* ✅
