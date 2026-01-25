"""README - Backend Application"""

# Stock Analysis System - Backend

## Overview
This is the backend application for the Stock Analysis System, built with FastAPI and Python.

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration management
│   ├── api/                    # API routes
│   ├── services/               # Business logic services
│   ├── models/                 # SQLAlchemy ORM models
│   ├── db/                     # Database utilities
│   │   ├── database.py         # Database connection & session management
│   │   ├── redis_cache.py      # Redis cache management
│   │   └── schema.sql          # Database schema definitions
│   └── utils/                  # Utility functions
├── tests/                      # Unit and integration tests
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables example
└── README.md                  # This file
```

## Setup

### 1. Create Python Virtual Environment

```bash
# Windows
python -m venv aistock_env
aistock_env\Scripts\activate

# Linux/Mac
python -m venv aistock_env
source aistock_env/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
# Copy the example .env file
cp .env.example .env

# Edit .env with your configuration
```

### 4. Initialize Database

```bash
# Create database and tables
python -c "from app.db.database import init_db; init_db()"
```

### 5. Run the Application

```bash
# Development mode with auto-reload
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using the main.py directly
python app/main.py
```

## API Documentation

Once the application is running, you can access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_models.py

# Run with verbose output
pytest -v
```

## Development

### Code Style
- Format code with Black: `black app/`
- Lint with Flake8: `flake8 app/`
- Type check with MyPy: `mypy app/`

### Database Migrations
Using Alembic for database migrations:

```bash
# Create initial migration
alembic init migrations

# Generate migration from model changes
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Environment Variables Reference

See `.env.example` for all available configuration options.

## Key Dependencies

- **FastAPI**: Web framework
- **Pydantic**: Data validation
- **SQLAlchemy**: ORM
- **pandas**: Data processing
- **akshare**: Stock data source
- **redis**: Caching
- **LangChain**: LLM integration
- **pytest**: Testing

## Common Issues

### Redis Connection Failed
- Ensure Redis is running: `redis-cli ping`
- Check REDIS_URL configuration in .env

### Database Connection Failed
- Ensure MySQL is running
- Verify DATABASE_URL in .env
- Check credentials

### Port Already in Use
- Change API_PORT in .env or use: `uvicorn app.main:app --port 8001`

## Next Steps

1. Implement API routes in `app/api/`
2. Add business logic services in `app/services/`
3. Create unit tests in `tests/`
4. Document API endpoints

## License

(Add your license here)
