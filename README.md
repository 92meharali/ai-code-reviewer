# AI Code Reviewer

An AI-powered GitHub application that automatically reviews Pull Requests using Large Language Models.

## Status

Early development. The backend API skeleton is in place with a health check endpoint.

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
│   ├── requirements.txt
│   └── requirements-dev.txt
└── README.md
```

## Local Setup

### Prerequisites

- Python 3.11+
- pip

### Backend

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

```bash
cd backend
pytest -v
```

## License

Private — all rights reserved.
