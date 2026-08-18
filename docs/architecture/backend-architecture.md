# Backend Architecture

## Approved stack

Use Python, Django, Django REST Framework, Django ORM, PostgreSQL, and JWT-based authentication. Celery/Redis are introduced only where asynchronous workloads required by the SDD are implemented.

## Logical module boundaries

| Module boundary | Approved responsibility | Later implementation phase |
| --- | --- | --- |
| Accounts and access | Users, roles, authentication, JWT, RBAC, account status | 2 |
| Academic goals | Student-owned goal validation and lifecycle | 3 |
| Study plans | Plans, tasks, retrieval, progress, revision history where approved | 5 |
| AI planning | Orchestrator, agents, aggregation, LLM integration, execution controls | 4 |
| Supervisor review | Plan review, feedback, approval/revision workflow | 6 |
| Audit and administration | Immutable audit events, user management, configuration, monitoring | 7 |
| Notifications | Completion, feedback, and system notifications; asynchronous dispatch | 8 |
| Reporting and export | Role-scoped reports and required PDF export | 8 |

These are logical boundaries, not a mandate to create a Django app for every row. During foundation work, related small responsibilities may be kept together when that preserves the approved separation of concerns.

## Backend conventions for later phases

- DRF views/viewsets, serializers, and permission classes own HTTP concerns, validation, and access enforcement.
- Domain services coordinate transactions and side effects; model code remains focused on persistence rules.
- The AI planning service invokes agents in approved sequence and is the only path that persists generated plans/tasks.
- Use Django ORM and database constraints for integrity. Wrap plan generation, review updates, and configuration changes in atomic transactions where specified.
- Record security-relevant and AI-relevant activity through controlled audit/logging services. Immutability enforcement design must be validated in the dedicated implementation phase.

## Phase 2 implementation

The `accounts` Django app implements the custom `AbstractUser` extension, the three approved role records, email/password registration with Student as the default role, JWT access/refresh authentication, refresh-token rotation/blacklisting, temporary failed-login lockout, account status enforcement, and Administrator-only user role/status management. It contains no goal, study-plan, AI, review, notification, audit-log, or export implementation.

## Not created in Phase 0

No Django project, apps, models, endpoints, authentication, task queue, LLM integration, or export mechanism has been created.
