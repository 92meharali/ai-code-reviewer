# AI Code Reviewer

![CI](https://github.com/92meharali/ai-code-reviewer/actions/workflows/ci.yml/badge.svg)

An AI-powered GitHub application that automatically reviews Pull Requests using Large Language Models.

## Status

Early development. The backend includes PostgreSQL persistence, a User model, GitHub OAuth login, development-only internal CRUD endpoints, and GitHub Actions CI.

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
│   │   ├── db/           # Database engine, sessions, ORM base
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── repositories/ # Data access layer
│   │   ├── schemas/      # Pydantic request/response models
│   │   ├── services/     # External integrations (GitHub OAuth)
│   │   └── main.py       # Application entry point
│   ├── alembic/          # Database migrations
│   ├── tests/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── requirements-dev.txt
├── docker-compose.yml
├── Makefile
├── .github/workflows/ci.yml
└── README.md
```

## Local Setup

### Prerequisites

- Docker and Docker Compose (recommended), or
- Python 3.11+ and pip

### Docker (recommended)

```bash
# Start the API and PostgreSQL
make up

# Apply database migrations
make migrate

# View logs
make logs

# Run tests
make test

# Check health (includes database status)
make health

# Stop services
make down
```

The API will be available at `http://localhost:8000`.

Run `make help` to see all available commands.

#### Internal user endpoints (development only)

After `make up` and `make migrate`, you can verify user CRUD:

```bash
# Create a user
curl -X POST http://localhost:8000/internal/users \
  -H "Content-Type: application/json" \
  -d '{"github_id": 12345, "username": "octocat", "email": "octocat@github.com"}'

# List users
curl http://localhost:8000/internal/users
```

### GitHub OAuth

1. Create a GitHub OAuth App at [https://github.com/settings/developers](https://github.com/settings/developers)
2. Set the callback URL to `http://localhost:8000/auth/github/callback`
3. Add credentials to `backend/.env`:

```bash
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret
GITHUB_OAUTH_REDIRECT_URI=http://localhost:8000/auth/github/callback
```

4. Start the API and open `http://localhost:8000/auth/github` in your browser

On success, `/auth/github/callback` returns the authenticated user as JSON and upserts the record in the database.

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

- Health check: `GET /health` (reports database connectivity)
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

## Continuous Integration

Every push and pull request to `main` triggers the CI workflow:

1. Build development and production Docker images
2. Start PostgreSQL
3. Run Alembic migrations
4. Execute the pytest suite

Workflow file: `.github/workflows/ci.yml`

## License

Private — all rights reserved.
