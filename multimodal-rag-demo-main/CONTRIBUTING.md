# Contributing to Multimodal RAG System

Thank you for your interest in contributing to the Multimodal RAG System! This document provides guidelines and information for contributors.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Architecture Overview](#architecture-overview)

## Getting Started

### Prerequisites

- Python 3.9+
- Docker and Docker Compose
- Git
- Basic understanding of:
  - FastAPI/async Python
  - Vector databases (FAISS)
  - Machine Learning concepts
  - Docker containerization

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/multimodal-rag-demo.git
   cd multimodal-rag-demo
   ```
3. Add the original repository as upstream:
   ```bash
   git remote add upstream https://github.com/original-owner/multimodal-rag-demo.git
   ```

## Development Environment

### Quick Setup

1. Copy environment variables:
   ```bash
   cp .env.example .env
   ```

2. Start development environment:
   ```bash
   docker-compose up -d
   ```

3. Install development dependencies:
   ```bash
   pip install -r requirements.api.txt -r requirements.test.txt
   ```

### Local Development Without Docker

If you prefer to run services locally:

1. Set up PostgreSQL and Redis locally
2. Update `.env` with local connection strings
3. Install Python dependencies
4. Run services individually:
   ```bash
   # API
   cd api && uvicorn main:app --reload --port 8000
   
   # UI
   cd ui && streamlit run app.py --server.port 8501
   
   # Worker
   cd worker && celery -A main worker --loglevel=info
   ```

## Code Standards

### Python Style

We follow PEP 8 with some modifications:

- Line length: 88 characters (Black default)
- Use type hints for all functions
- Docstrings for all public functions and classes
- Use async/await for I/O operations

### Code Formatting

We use the following tools:

```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8 api/ ui/ worker/

# Type checking
mypy api/ --ignore-missing-imports
```

### Pre-commit Hooks

Install pre-commit hooks to automatically check code before commits:

```bash
pip install pre-commit
pre-commit install
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=api --cov-report=html

# Run specific test file
pytest tests/test_api.py -v

# Run integration tests
pytest tests/integration/ -v
```

### Test Structure

- `tests/test_api.py` - API endpoint tests
- `tests/test_services.py` - Service layer tests
- `tests/test_ui.py` - UI component tests
- `tests/test_worker.py` - Worker task tests
- `tests/integration/` - End-to-end integration tests

### Writing Tests

- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)
- Mock external dependencies
- Aim for >90% code coverage
- Include both positive and negative test cases

Example test:

```python
def test_document_upload_success(self, client, headers, sample_pdf):
    """Test successful document upload with valid PDF"""
    with patch('api.services.document_service.DocumentService.process_document_async') as mock_process:
        mock_process.return_value = {"task_id": "test-task-123", "status": "pending"}
        
        with open(sample_pdf, 'rb') as f:
            files = {"file": ("test.pdf", f, "application/pdf")}
            response = client.post("/documents/upload", files=files, headers=headers)
        
        assert response.status_code == 202
        data = response.json()
        assert "task_id" in data
```

## Pull Request Process

### Before Submitting

1. Ensure all tests pass
2. Update documentation if needed
3. Add/update tests for new functionality
4. Run code formatting tools
5. Check that your changes don't break existing functionality

### PR Guidelines

1. **Title**: Use clear, descriptive titles
   - ✅ "Add multimodal search endpoint with image support"
   - ❌ "Fix stuff"

2. **Description**: Include:
   - What changes were made
   - Why the changes were necessary
   - How to test the changes
   - Any breaking changes

3. **Size**: Keep PRs focused and reasonably sized
   - Prefer multiple small PRs over one large PR
   - If large changes are necessary, break them into logical commits

4. **Reviews**: 
   - Request reviews from relevant team members
   - Address all feedback before merging
   - Ensure CI checks pass

### Commit Messages

Use conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(api): add multimodal search endpoint

Add endpoint that accepts both text and image queries for
enhanced document search capabilities.

Closes #123
```

## Issue Reporting

### Bug Reports

When reporting bugs, include:

1. **Environment**: OS, Python version, Docker version
2. **Steps to reproduce**: Clear, step-by-step instructions
3. **Expected behavior**: What you expected to happen
4. **Actual behavior**: What actually happened
5. **Logs/Screenshots**: Any relevant error messages or screenshots
6. **Additional context**: Any other relevant information

### Feature Requests

For new features, include:

1. **Problem statement**: What problem does this solve?
2. **Proposed solution**: How would you like it to work?
3. **Alternatives considered**: Other approaches you've thought about
4. **Use cases**: Real-world scenarios where this would be useful

## Architecture Overview

### System Components

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    Nginx    │    │  Streamlit  │    │   FastAPI   │
│   (Proxy)   │◄──►│     UI      │◄──►│     API     │
└─────────────┘    └─────────────┘    └─────────────┘
                                              │
                   ┌─────────────┐    ┌─────────────┐
                   │   Celery    │◄──►│  PostgreSQL │
                   │   Worker    │    │  Database   │
                   └─────────────┘    └─────────────┘
                          │
                   ┌─────────────┐    ┌─────────────┐
                   │    Redis    │    │    FAISS    │
                   │   Broker    │    │   Vector    │
                   └─────────────┘    │   Store     │
                                     └─────────────┘
```

### Key Design Principles

1. **Microservices Architecture**: Separate services for API, UI, and worker
2. **Async Processing**: Long-running tasks handled asynchronously
3. **API-First**: All functionality exposed via REST API
4. **Containerization**: All components containerized for easy deployment
5. **Monitoring**: Comprehensive logging and metrics collection
6. **Security**: API key authentication, rate limiting, input validation

### Adding New Features

When adding new features:

1. **API Changes**: Update OpenAPI spec in `api/openapi.yaml`
2. **Database Changes**: Create migration scripts in `scripts/migrations/`
3. **Tests**: Add comprehensive tests for new functionality
4. **Documentation**: Update relevant documentation
5. **N8N Integration**: Consider webhook integration points

### Code Organization

```
api/
├── main.py              # FastAPI application
├── models.py            # Pydantic models
├── config.py            # Configuration
├── database.py          # Database setup
└── services/            # Business logic
    ├── auth.py
    ├── document_service.py
    ├── search_service.py
    └── task_manager.py

ui/
├── app.py               # Streamlit application
└── components/          # UI components

worker/
├── main.py              # Celery application
└── tasks.py             # Task definitions

tests/
├── test_api.py          # API tests
├── test_ui.py           # UI tests
├── test_worker.py       # Worker tests
└── integration/         # Integration tests
```

## Questions?

If you have questions about contributing:

1. Check existing issues and documentation
2. Ask in discussions or create an issue
3. Reach out to maintainers

Thank you for contributing to the Multimodal RAG System! 🚀
