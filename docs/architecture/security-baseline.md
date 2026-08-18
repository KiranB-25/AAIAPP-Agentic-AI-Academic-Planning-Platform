# Security Baseline

## Required controls from the SRS/SDD

- JWT authentication with expiry, refresh-token handling/rotation, optional blacklist support, and secure token transmission.
- RBAC for Student, Supervisor, and Administrator; endpoint-level and object-level ownership/assignment validation.
- Django password hashing (PBKDF2 stated), password complexity rules, inactive-account denial, login attempt logging, and rate limiting/temporary lock policy where specified.
- HTTPS using TLS 1.2+, HSTS, restrictive CORS allow-lists, CSRF middleware, and secure/HttpOnly cookie configuration where applicable.
- Secure environment-variable storage for LLM keys, JWT signing material, database credentials, and encryption keys. Secrets must not be committed or sent to clients.
- Atomic database operations for AI plan generation and other specified multi-record updates; idempotency identifiers for generation requests.
- Immutable audit and AI execution logging, including relevant actor/action/time and network/client context where available.
- Encryption at rest for specified sensitive data, with AES-256 called for sensitive database fields; key separation and six-month key rotation are SDD requirements for production-oriented deployment.
- Suspicious-activity monitoring, backups, retention, and access-limited logs as specified.

## Implementation posture

Security controls will be implemented and tested in the phases that introduce their features, then hardened in Phase 9. AI processing stays server-side; generated outputs must be validated before persistence. No security mechanism is implemented in Phase 0.

## Decision Required

- The SDD calls for field-level AES-256 encryption but does not identify the exact fields/approved cryptographic package or key-management service. Confirm the production deployment approach before implementation.
- The SDD gives both configurable session timeout and JWT expiry but does not define authoritative durations beyond an example of 15 minutes inactivity. Confirm policy values.
