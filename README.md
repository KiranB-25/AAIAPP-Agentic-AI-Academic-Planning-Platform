# Agentic AI Academic Planning Platform (AAIAPP)

AAIAPP is a BSCS Final Year Project for creating structured academic study plans from student goals through controlled, modular AI orchestration.

## Project status

The repository is currently at **Phase 2: authentication, user management, and RBAC**. The foundation includes a Django REST health API and a React application shell. Academic planning, AI, reporting, notifications, and other business features are intentionally deferred to later phases.

## Authoritative specifications

The approved Software Requirements Specification (SRS) and Software Design Description (SDD), supplied by the project owner, are the sole authority for requirements and architecture. The Phase 0 documentation summarizes implementation boundaries; it does not replace those approved documents.

## Approved direction

- Backend: Python, Django, Django REST Framework, Django ORM, PostgreSQL, JWT
- Frontend: React, TypeScript, Vite, Tailwind CSS, shadcn/ui, Lucide React
- AI: API-based LLM integration through `AgentOrchestrator`, `PlannerAgent`, `ContentGeneratorAgent`, `EvaluationAgent`, and plan aggregation
- Async processing: Celery with Redis where required by the SDD
- Reporting: PDF export is required; CSV export is intentionally deferred

## Repository structure

```text
backend/       Django project, configuration, API foundation, and backend tests
frontend/      React + TypeScript + Vite application shell
docs/          Approved architecture baseline and implementation roadmap
```

## Local setup

Prerequisites: Python 3.10+ (the current environment uses Python 3.14), Node.js, npm, and a running PostgreSQL server.

1. Copy `.env.example` to `.env` and set a unique `DJANGO_SECRET_KEY` plus local PostgreSQL credentials. The example CORS allow-list covers Vite at both `localhost:5173` and `127.0.0.1:5173`.
2. Create and activate a virtual environment, then install backend dependencies:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r backend/requirements.txt
   ```

3. Create the database and PostgreSQL role matching `.env`, then initialize Django:

   ```bash
   cd backend
   python manage.py migrate
   python manage.py runserver
   ```

4. In another terminal, configure and run the frontend:

   ```bash
   cd frontend
   cp .env.example .env
   npm install
   npm run dev
   ```

The development frontend uses `VITE_API_BASE_URL` (default `http://127.0.0.1:8000`) and calls the backend health endpoint.

## Verification commands

```bash
# backend, from backend/
python manage.py check
python manage.py test

# frontend, from frontend/
npm run build
```

## Available API endpoint

`GET /api/health/` returns:

```json
{ "status": "ok" }
```

## Authentication API foundation

- `POST /api/auth/register/` — creates a Student account from `name`, `email`, and `password`.
- `POST /api/auth/login/` — authenticates email/password and returns JWT access/refresh tokens plus the safe user profile.
- `POST /api/auth/token/refresh/` — rotates a refresh token.
- `POST /api/auth/logout/` — blacklists a refresh token; requires the access token in the `Authorization: Bearer` header.
- `GET /api/auth/me/` — returns the authenticated user.
- `GET /api/auth/users/` and `PATCH /api/auth/users/{id}/` — Administrator-only user listing, role assignment, and account-status management.

The frontend starts at `/login/`, stores the authenticated session only for the current browser session, and redirects users to the approved role foundations: `/student/`, `/supervisor/`, or `/admin/`.

## Documentation

- [Architecture baseline](docs/architecture/architecture-baseline.md)
- [Backend architecture](docs/architecture/backend-architecture.md)
- [Frontend architecture](docs/architecture/frontend-architecture.md)
- [Database baseline](docs/architecture/database-baseline.md)
- [AI orchestration](docs/architecture/ai-orchestration.md)
- [API baseline](docs/architecture/api-baseline.md)
- [Security baseline](docs/architecture/security-baseline.md)
- [Implementation roadmap](docs/implementation-roadmap.md)

See [AGENTS.md](AGENTS.md) for instructions that apply to future development sessions.
