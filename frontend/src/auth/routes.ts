import type { UserRole } from "../types/auth";

export const LOGIN_PATH = "/login/";

export const roleHome: Record<UserRole, string> = {
  student: "/student/",
  supervisor: "/supervisor/",
  administrator: "/admin/",
};

export function roleForPath(pathname: string): UserRole | null {
  if (pathname.startsWith("/student")) return "student";
  if (pathname.startsWith("/supervisor")) return "supervisor";
  if (pathname.startsWith("/admin")) return "administrator";
  return null;
}

export function navigate(pathname: string) {
  window.history.pushState({}, "", pathname);
  queueMicrotask(() => window.dispatchEvent(new PopStateEvent("popstate")));
}
