# AAIAPP Development Instructions

## Authority and scope

- The approved SRS and SDD are the authoritative specifications for the Agentic AI Academic Planning Platform (AAIAPP). Treat the copies supplied by the project owner as the source of truth.
- Do not invent, remove, reinterpret, or redesign requirements. When the documents are ambiguous or conflict, document the uncertainty as **Decision Required** and ask the project owner; do not silently choose a product requirement.
- Work phase by phase according to `docs/implementation-roadmap.md`. Do not prematurely implement later-phase features.
- Preserve existing working functionality. Do not rewrite it unless a change is necessary and approved.

## Technology and boundaries

- Backend: Python, Django, Django REST Framework, Django ORM, PostgreSQL, and JWT authentication.
- Frontend: React, TypeScript, Vite, Tailwind CSS, shadcn/ui, and Lucide React. Use TypeScript consistently.
- Keep frontend presentation concerns separate from backend business logic and API concerns.
- Follow Django and DRF conventions: apps with clear ownership, serializers for validation, permissions for authorization, and transactions for multi-record operations.
- Keep AI components modular: `AgentOrchestrator`, `PlannerAgent`, `ContentGeneratorAgent`, `EvaluationAgent`, and plan aggregation.
- Agents must not bypass the orchestrator or directly persist data. Persistence remains controlled by the Django application layer/orchestration workflow.

## Security and quality

- Never commit secrets, API keys, passwords, tokens, or populated environment files. Use environment variables and committed example files only.
- Respect the SRS/SDD security baseline: JWT, RBAC, ownership checks, password hashing, HTTPS/CORS/CSRF configuration, audit logging, atomic operations, and protected AI credentials.
- Run relevant tests after meaningful implementation changes and report the result.
- PDF export is required in its scheduled phase. CSV export is currently skipped and must not be implemented.
- Report uncertainty, implementation trade-offs, and unverified assumptions clearly rather than presenting them as approved facts.
