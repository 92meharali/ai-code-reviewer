# AI Code Reviewer

An AI-powered GitHub application that automatically reviews Pull Requests using Large Language Models.

## Status

Early development. The backend API skeleton is in place with a health check endpoint and Docker-based local development.

## Tech Stack

| Layer          | Technology                          |
|----------------|-------------------------------------|
| Backend        | Python, FastAPI, SQLAlchemy         |
| Database       | PostgreSQL, Alembic                 |
| Task Queue     | Celery, Redis                       |
| Frontend       | Next.js, React, TypeScript          |
| Infrastructure | Docker, Docker Compose, GitHub Actions |
| AI             | OpenAI (multi-provider support planned) |

## Project Structure

```
ai-code-reviewer/
├── backend/
│   ├── app/
│   │   ├── api/          # HTTP routes
│   │   ├── core/         # Config, logging, shared utilities
│   │   └── main.py       # Application entry point
│   ├── tests/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── requirements-dev.txt
├── docker-compose.yml
├── Makefile
└── README.md
```

## Local Setup

### Prerequisites

- Docker and Docker Compose (recommended), or
- Python 3.11+ and pip

### Docker (recommended)

```bash
# Start the API with hot reload
make up

# View logs
make logs

# Run tests
make test

# Check health
make health

# Stop services
make down
```

The API will be available at `http://localhost:8000`.

Run `make help` to see all available commands.

### Backend (without Docker)

```bash
cd backend

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt

# Copy environment variables
cp .env.example .env

# Run the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

- Health check: `GET /health`
- Interactive docs: `http://localhost:8000/docs`

### Running Tests

With Docker:

```bash
make test
```

Without Docker:

```bash
cd backend
pytest -v
```

## License

Private — all rights reserved.
