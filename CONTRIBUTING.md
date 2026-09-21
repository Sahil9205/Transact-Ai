# Contributing to TransactAI

Thank you for your interest in contributing to **TransactAI**! We welcome bug reports, feature enhancements, documentation improvements, and architectural optimizations.

---

## Code of Conduct

TransactAI is dedicated to providing an inclusive, harassment-free environment for everyone. Please be respectful, professional, and collaborative in all discussions and pull requests.

---

## Getting Started

### Prerequisites
- **Python**: 3.12 or higher
- **Node.js**: 20.x or higher
- **Git**: 2.30+

### 1. Repository Setup

Clone the repository and set up a Python virtual environment:

```bash
git clone https://github.com/Sahil9205/Transact-Ai.git
cd Transact-Ai

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# macOS / Linux:
source .venv/bin/activate

# Install dependencies including development tooling
pip install --upgrade pip
pip install -e ".[dev]"
```

### 2. Frontend Setup

```bash
cd frontend
npm install
cd ..
```

---

## Development Workflow

### Running the Services Locally

1. **Start the FastAPI Backend**:
   ```bash
   uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000 --reload
   ```
   Interactive Swagger documentation is available at `http://localhost:8000/docs`.

2. **Start the Next.js Frontend**:
   ```bash
   cd frontend
   npm run dev
   ```
   Access the web interface at `http://localhost:3000`.

---

## Quality Standards & CI

All submissions must satisfy our automated continuous integration checks before being merged:

### 1. Code Formatting & Linting

We use [Ruff](https://astral.sh/ruff) for lightning-fast Python linting:

```bash
# Check code style and formatting
ruff check app/ tests/

# Automatically fix supported linting violations
ruff check --fix app/ tests/
```

### 2. Type Checking

We use [Mypy](https://mypy-lang.org/) for strict typing compliance:

```bash
mypy app/
```

### 3. Automated Test Suite & Coverage

Our codebase maintains >= 80% test coverage:

```bash
# Run unit tests with coverage reporting
pytest tests/unit --cov=app --cov-report=term-missing

# Run end-to-end integration tests
pytest tests/integration/
```

### 4. Frontend Build

Ensure the Next.js application compiles with zero TypeScript or build errors:

```bash
cd frontend
npm run build
cd ..
```

---

## Commit Guidelines

We enforce the [Conventional Commits](https://www.conventionalcommits.org/) standard. Each commit should follow the format:

```text
<type>(<scope>): <short imperative summary>
```

### Supported Types
- `feat`: A new user-facing feature or enhancement.
- `fix`: A bug fix or regression repair.
- `docs`: Documentation updates, guides, or comments.
- `test`: Adding or refactoring unit/integration tests.
- `ci`: CI/CD workflows, build scripts, or dependency tooling.
- `refactor`: Code reorganization with no behavioral change.

---

## Pull Request Process

1. Create a descriptive feature branch from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```
2. Implement your changes, ensuring new logic is covered with unit tests.
3. Verify that `ruff check`, `pytest`, and `npm run build` all pass cleanly.
4. Push your branch to GitHub and open a Pull Request against `main`.
5. Clearly articulate the rationale, architectural impact, and verification steps in your PR description.
