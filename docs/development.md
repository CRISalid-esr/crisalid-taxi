# 🛠️ Local Development, Testing & Code Quality Guide

This document details the local development environment setup, dependency management, and code quality tools (linters, testers, formatters).

---

## 💻 Local Environment Setup

### 1. Prerequisites

Ensure you have Python 3.11+ and the modern Python package management tool `uv` installed on your machine.

#### Install `uv` if necessary:
```bash
pip install uv
```

### 2. Installing Dependencies

Synchronize the local virtual environment `.venv` using `uv`:

```bash
# To install only production dependencies
uv sync

# To install development dependencies (tests, linters, etc.)
uv sync --all-extras
```

---

## 📦 Dependency Management

The project uses `pyproject.toml` to declare dependencies and a frozen `uv.lock` file to guarantee reproducibility.

> ⚠️ **Important:** Never manually edit the `uv.lock` file. Let the `uv` utilities handle it.

### Useful commands to manage dependencies:
```bash
# Add a production dependency
uv add <package-name>

# Add an optional development dependency
uv add --optional dev <package-name>

# Remove a dependency
uv remove <package-name>
```

---

## ⚡ Start the API locally (Without Docker)

To run the API server locally in automatic reload mode (Hot Reload):

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🧪 Code Validation & Quality

Before submitting code, please run the following code quality checks.

### 1. Run the Test Suite
```bash
# Run tests (unit & integration)
uv run pytest tests/ -v

# Run tests with coverage calculation and HTML report
uv run pytest tests/ -v --cov=app --cov-report=html
```

### 2. Code Formatting (Black & Isort)
The project uses `black` for formatting and `isort` for import sorting.
```bash
# Check if any files need formatting
uv run black --check app/ tests/

# Automatically apply Black formatting
uv run black app/ tests/

# Automatically sort imports
uv run isort app/ tests/
```

### 3. Static Analysis & Linting (Pylint)
```bash
# Analyze the code with Pylint
uv run pylint app/
```

### 4. Type Checking (Mypy)
```bash
# Static type analysis
uv run mypy app/ tests/
```
