# AAIAPP Implementation Roadmap

This roadmap sequences implementation of the approved SRS/SDD. It does not add or alter requirements. Each phase should be split into small, testable tasks as needed, and unresolved items in the architecture documentation require project-owner direction before implementation.

| Phase | Focus | Approved outcomes |
| --- | --- | --- |
| 0 | Analysis and baseline | Repository assessment, architecture documents, Codex instructions, roadmap; no features |
| 1 | Foundation | Django/DRF and React/TypeScript/Vite foundations, PostgreSQL configuration, environment examples, development tooling and test setup |
| 2 | Authentication and RBAC | User/role foundation, registration/login policy, JWT, role and ownership permissions, security logging |
| 3 | Data models and goals | Approved core models and migrations; academic-goal validation and permitted lifecycle operations |
| 4 | Agentic AI planning | Orchestrator, modular agents, controlled LLM integration, validation, aggregation, execution logs, atomic/idempotent generation workflow |
| 5 | Study plans and progress | Plan/task retrieval, status and approved task-completion/progress behavior, student plan views/API support |
| 6 | Supervisor workflow | Authorized plan review, feedback, approval/revision behavior, associated audit trail |
| 7 | Administration and monitoring | User/status/role administration, approved AI configuration, audit access, AI execution monitoring |
| 8 | Notifications, reporting, PDF | Required notification workflow, role-scoped reports/analytics, required PDF plan export; CSV remains out of scope |
| 9 | Security, testing, integration | Security hardening, unit/integration/system/security testing, performance checks, external integration validation |
| 10 | UI, deployment, FYP closeout | UI/UX refinement, accessibility/responsiveness, deployment preparation, documentation, demonstration and final verification |

## Phase gates

- Do not begin feature implementation before its prerequisite data, security, and contract decisions are complete.
- Validate against the SRS/SDD and run appropriate tests after meaningful changes.
- Treat unresolved design items as Decision Required, never as implicit approval.
