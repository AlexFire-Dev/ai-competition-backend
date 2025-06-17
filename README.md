# AI Competition Backend

This repository contains the backend for the AI Bomberman competition. The
service is built with **FastAPI**.

## Project structure

- **app/** – main FastAPI application
  - **api/** – REST and WebSocket routes
  - **core/** – configuration and database setup
  - **crud/** – database access helpers
  - **services/** – WebSocket logic and Celery tasks
  - **celery_app.py** – Celery configuration
  - **main.py** – FastAPI entry point
  - **models.py**, **schemas.py** – SQLAlchemy models and Pydantic schemas
- **bomberman/** – minimal game logic
- **alembic/** – database migrations
- **start.sh** – script that runs Uvicorn
- **Dockerfile**, **docker-compose.yml** – container setup

## Running locally

1. Create a `.env` file with database and secret settings:
   ```
   SECRET_KEY=your-secret-key
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   DATABASE_URL=postgresql://user:password@localhost:5432/mydb
   REDIS_HOST=localhost
   REDIS_PORT=6379
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the server:
   ```bash
   ./start.sh
   ```
   The API will be available at `http://localhost:8000`.

To run inside Docker:
```bash
docker compose up --build
```

## Deployed services

- Frontend: <https://hse.af.shvarev.com>
- Backend docs: <https://course.af.shvarev.com/docs#/>