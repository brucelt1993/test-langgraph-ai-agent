# Backend Tests

This directory contains all tests for the AI Agent backend application.

## Test Structure

```
tests/
├── conftest.py         # Pytest fixtures and configuration
├── test_auth/         # Authentication tests
├── test_chat/         # Chat functionality tests
├── test_agents/       # AI agent tests
├── test_services/     # Service layer tests
├── test_repositories/ # Repository tests
└── test_api/          # API endpoint tests
```

## Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test file
uv run pytest tests/test_auth/test_auth_service.py

# Run tests in parallel
uv run pytest -n auto

# Run tests with verbose output
uv run pytest -v
```

## Test Database

Tests use SQLite in-memory database for fast execution and isolation.
Each test gets a clean database instance through fixtures.