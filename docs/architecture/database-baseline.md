# Database Baseline

## Approved core entities

AAIAPP uses PostgreSQL through Django ORM. The approved relational design identifies the following entities.

| Entity | Approved purpose | Key relationship |
| --- | --- | --- |
| Role | Access category and permission boundary | One Role to many Users |
| User | Authenticated actor; custom `AbstractUser` extension in SDD | One User to many AcademicGoals and AuditLogs |
| AcademicGoal | Student academic objective | Belongs to one User; source for StudyPlan |
| StudyPlan | AI-generated plan and status/summary metadata | Derived from AcademicGoal; parent of tasks, feedback, AI logs |
| PlanTask | Weekly/milestone activity | Many tasks to one StudyPlan |
| SupervisorFeedback | Supervisor’s non-editable review comments | Belongs to StudyPlan and supervisor User |
| AuditLog | Critical user/system action record | Belongs to User where applicable |
| AIExecutionLog | AI processing/audit record | Associated with StudyPlan where applicable |

```text
Role 1 ── * User 1 ── * AcademicGoal ── StudyPlan 1 ── * PlanTask
                   └── * AuditLog                  ├── * SupervisorFeedback (from User/Supervisor)
                                                    └── * AIExecutionLog
```

The SRS describes normalized storage, foreign keys, referential integrity, timestamps, controlled transactions, and secure password hashing. The SDD additionally calls for immutable AI execution logs and records audit/logging contexts such as action, timestamp, IP, and user agent where applicable.

## Decision Required / ambiguity register

- The SRS says one AcademicGoal generates one StudyPlan, while the SDD says StudyPlan has a “one-to-one or one-to-many” relationship with AcademicGoal. Confirm the implemented cardinality, including how revision cycles are represented.
- The SRS states cascade deletion for dependent plans, but SDD says plans/logs are retained for at least five years and logs are immutable/non-deletable. Confirm the deletion/retention policy and whether soft deletion is intended.
- SRS names `method` on PlanTask; SDD lists task title/description/week and does not consistently specify `method`. Confirm final fields before model design.
- Supervisor assignment is referenced for review authorization, but no entity/relationship assigning supervisors to students or plans is specified. Confirm the approved ownership/assignment source before implementation.
