# API Planning Baseline

The SDD defines RESTful DRF APIs secured with JWT, serializer validation, RBAC, ownership checks, structured JSON responses, atomic operations, and idempotency for plan generation. This document maps required API domains; it deliberately does not fix URL paths, HTTP verbs, or undocumented payload fields.

| API domain | Approved operations / outcome |
| --- | --- |
| Authentication | Registration, login, JWT access/refresh lifecycle, active-status checks, login activity logging |
| Goal management | Student goal submission, permitted pre-generation modification, validation, ownership control |
| Study plans | Generated plan retrieval, role-scoped access, status/task/progress data, required PDF export in its later phase |
| Plan generation | Authenticated student submits valid goal data; orchestrated AI generation returns/persists validated plan and execution information |
| Supervisor review | Authorized supervisor retrieves reviewable plan, submits feedback, approves or requests revision, triggers student notification |
| Administration | User/role/status management, approved AI configuration management, audit and execution-log access |
| Reporting | Role-scoped read-only summaries and analytics in later phases |

## API execution rules

- Plan generation must use a unique request/execution identifier to prevent duplicate processing and replay, as specified in the SDD.
- Responses and errors must be structured JSON. Failed validation or AI operations must be logged and must not leave partial records.
- Filtering/pagination are approved for study-plan retrieval. Rate limiting applies to sensitive endpoints and plan generation as specified.
- CSV export is not planned for this stage; PDF export remains required in Phase 8.

## Decision Required

- Exact endpoint paths, response contracts, registration policy for Supervisor/Administrator accounts, and JWT refresh/blacklist package settings are not specified. Define these in the API implementation phase without altering the approved functional scope.
