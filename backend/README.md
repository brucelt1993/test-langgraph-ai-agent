# AI Agent Backend

AI Agent Backend with FastAPI and LangGraph

## Features

- FastAPI web framework
- LangGraph for AI agent workflows
- SQLAlchemy for database management
- JWT authentication
- OpenAI integration
- Weather API integration
- Real-time streaming support

## Installation

1. Install dependencies:
```bash
uv sync
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Initialize database:
```bash
uv run python manage_db.py init
```

4. Start the development server:
```bash
uv run fastapi dev main.py
```

## API Documentation

Once running, visit:
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Environment Variables

Required environment variables:
- `OPENAI_API_KEY`: Your OpenAI API key
- `SECRET_KEY`: Secret key for JWT tokens
- `DATABASE_URL`: Database connection URL

See `.env.example` for all available configuration options.

## Development

Run tests:
```bash
uv run pytest
```

Format code:
```bash
uv run black app/
uv run isort app/
```

Type checking:
```bash
uv run mypy app/
```