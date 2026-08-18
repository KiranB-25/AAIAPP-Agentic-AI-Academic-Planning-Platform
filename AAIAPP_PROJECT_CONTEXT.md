# AAIAPP PROJECT CONTEXT


## Project Name

Agentic AI Academic Planning Platform (AAIAPP)


## Purpose

AAIAPP is an AI-powered academic planning platform where students provide academic goals and constraints, and intelligent agents generate personalized study plans.


## Technology Stack

Backend:
- Django
- Django REST Framework
- PostgreSQL

Frontend:
- React
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui


## User Roles

### Student

Capabilities:
- Create academic goals
- Generate study plans
- Track progress
- View supervisor feedback


### Supervisor

Capabilities:
- View assigned students
- Review plans
- Approve or request revisions


### Administrator

Capabilities:
- Manage users
- Manage roles
- View audit information


## AI Architecture

Approved workflow:

Student Goal

↓

Agent Orchestrator

↓

Planner Agent

↓

Content Generator Agent

↓

Evaluation Agent

↓

Plan Aggregator

↓

Study Plan


## Completed Features

Completed:
- Authentication
- JWT
- Role-based access control
- Academic goals
- Study plans
- Student progress
- Supervisor reviews
- Notifications
- Audit logging
- PDF export


## Current Missing Features

- Real LLM integration
- Real AI reasoning
- Personalized AI planning
- Professional UI redesign
- AI monitoring dashboard


## Development Rules

Always:

- Preserve existing architecture
- Do not break completed features
- Follow SRS/SDD architecture
- Make changes phase by phase
- Provide final implementation report


Never:

- Rewrite the whole application
- Change backend unnecessarily
- Introduce unrelated features