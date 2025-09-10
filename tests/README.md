# Integration and E2E Tests

This directory contains integration tests and end-to-end tests for the AI Agent application.

## Directory Structure

```
tests/
├── integration/           # API integration tests
│   ├── conftest.py       # Integration test fixtures
│   ├── test_auth_flow.py # Authentication workflow tests
│   ├── test_chat_flow.py # Chat workflow tests
│   └── test_api_contracts.py # API contract tests
├── e2e/                  # End-to-end tests
│   ├── playwright.config.ts # Playwright configuration
│   ├── fixtures/         # Test fixtures and utilities
│   ├── tests/           # E2E test files
│   └── utils/           # Test helper utilities
└── docker/              # Test environment containers
    └── docker-compose.test.yml
```

## Integration Tests

Integration tests verify API workflows and data flows between components.

### Running Integration Tests

```bash
# Backend integration tests
cd backend
uv run pytest tests/integration/ -v

# Run with test database
DATABASE_URL=postgresql://test:test@localhost:5433/test_db uv run pytest tests/integration/
```

## E2E Tests

End-to-end tests validate complete user journeys using Playwright.

### Running E2E Tests

```bash
# Install Playwright
cd tests/e2e
npm install
npx playwright install

# Run E2E tests
npm run test:e2e

# Run with UI
npm run test:e2e:ui

# Run specific test
npx playwright test tests/auth-flow.spec.ts
```

## Test Data Management

- Integration tests use isolated test databases
- E2E tests use containerized environments
- Test data is automatically cleaned up after each test
- Fixtures provide consistent test data across test runs