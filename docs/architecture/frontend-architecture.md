# Frontend Architecture

## Approved stack and role scope

The future frontend uses React, TypeScript, Vite, Tailwind CSS, shadcn/ui, and Lucide React. It will provide role-specific experiences for Student, Supervisor, and Administrator, consistent with the SDD. It does not implement screens in Phase 0.

## Planned conventions

```text
src/
  components/     reusable presentational UI and shadcn/ui compositions
  pages/          route-level, role-oriented screens
  layouts/        shared authenticated and public layouts
  services/       typed REST API client modules
  hooks/          reusable UI/data-access hooks
  types/          TypeScript API/domain contracts
  lib/            utilities and shared configuration
```

Forms should use typed field models, client-side usability validation, and server validation messages. API services own transport and token attachment; pages do not embed HTTP details. Components must model loading, empty, error, and success states. Future notifications use a centralized mechanism, and data displays use reusable cards, badges, tables, dialogs, tabs, progress indicators, and skeletons where appropriate.

## Design direction

Use a centralized, responsive, accessible design system: professional, modern, academic, clean, and low-clutter. Prefer shadcn/ui before creating custom primitives; use Lucide React for icons. Future UI work must support SDD navigation features such as role-based sidebar/dashboard patterns, feedback/status states, responsive layouts, and WCAG 2.1-oriented semantic and contrast practices.

## Phase 2 implementation

The frontend now provides a typed authentication service and session context, a responsive login page, protected role-route foundations, and logout. The role landing pages are intentional placeholders with no dashboard data or domain functionality.

## Explicitly deferred

Dashboards, registration UI, goal forms, study-plan screens, progress tracking, notifications, exports, and administrative screens are later-phase work.
