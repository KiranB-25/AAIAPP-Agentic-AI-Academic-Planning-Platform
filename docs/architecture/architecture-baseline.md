# AAIAPP Architecture Baseline

## Scope and authority

This baseline records the architecture approved in the project SRS and SDD. It is an implementation guide, not a replacement for either document. No application behavior is implemented by this document.

## Purpose and actors

AAIAPP is a secure, web-based academic planning platform. Students submit academic goals and receive structured, milestone-based study plans. Supervisors review plans and provide feedback. Administrators manage users, configuration, and system/audit visibility. The SRS also identifies an optional System Auditor role; the SDD’s primary role model identifies Student, Supervisor, and Administrator.

## Approved layered flow

```text
React web client
       ↓ HTTPS + JWT
REST API (Django REST Framework)
       ↓
Django application layer
  ├─ authentication and RBAC
  ├─ academic goals, plans, reviews, audit controls
  └─ AgentOrchestrator
       ↓
PlannerAgent → ContentGeneratorAgent → EvaluationAgent → Plan Aggregation
       ↓
Django ORM / controlled persistence
       ↓
PostgreSQL
```

The AI integration layer invokes the API-based LLM only from the server. For high-latency work specified by the SDD, Celery workers and Redis handle asynchronous AI processing, exports, and notifications. The communication layer may use SMTP and optionally an SMS gateway. LMS, ERP, calendar, and cloud storage integrations are future/optional and are not Phase 0 implementation scope.

## Key architectural rules

- Presentation, application, AI orchestration, integration, and data responsibilities remain separated.
- The API validates authenticated requests and enforces RBAC before business or AI processing.
- AI outputs are validated and aggregated before database persistence.
- Agents do not directly access the database; the orchestrated application workflow controls persistence and logs.
- Multi-record plan generation follows atomic transaction boundaries; execution and audit records support accountability.

## Requirements coverage

The baseline covers SRS functional requirements FR-1 to FR-20; non-functional concerns including performance, reliability, usability, scalability, portability, and security; SDD decomposition, workflow, UI, API, and deployment direction. Detailed decisions are located in the companion architecture documents.

## Decision Required

- The SRS describes an optional System Auditor, while the SDD’s RBAC sections consistently define three primary roles. Confirm whether System Auditor is an initial-release role or a future/optional role.
- The SDD mentions real-time in-app alerts but does not prescribe a transport mechanism. A later phase needs project-owner direction before choosing polling, WebSockets, or another approach.
