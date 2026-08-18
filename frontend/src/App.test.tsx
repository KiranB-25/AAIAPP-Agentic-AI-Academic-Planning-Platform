import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";
import { sessionKey } from "./auth/session-store";
import type { AuthSession, AuthenticatedUser } from "./types/auth";

const users: Record<"student" | "supervisor" | "administrator", AuthenticatedUser> = {
  student: { id: 1, name: "Student", email: "student@example.com", role: "student", status: "active" },
  supervisor: { id: 2, name: "Supervisor", email: "supervisor@example.com", role: "supervisor", status: "active" },
  administrator: { id: 3, name: "Administrator", email: "admin@example.com", role: "administrator", status: "active" },
};

function response(status: number, body?: unknown) {
  return new Response(body === undefined ? null : JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function storedSession(role: keyof typeof users): AuthSession {
  return { access: "access", refresh: "refresh", user: users[role] };
}

describe("authentication UI", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    sessionStorage.clear();
    window.history.replaceState({}, "", "/login/");
  });

  it("renders the canonical login page directly", () => {
    render(<App />);
    expect(screen.getByRole("heading", { name: "Sign in to AAIAPP" })).toBeInTheDocument();
  });

  it("shows backend authentication errors", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(response(401, { detail: "Invalid email or password." }));
    render(<App />);
    await userEvent.type(screen.getByLabelText("Email address"), "student@example.com");
    await userEvent.type(screen.getByLabelText("Password"), "wrong-password");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Invalid email or password.");
  });

  it("shows a loading state while login is pending", async () => {
    let resolveLogin!: (value: Response) => void;
    vi.spyOn(globalThis, "fetch").mockImplementation(() => new Promise((resolve) => { resolveLogin = resolve; }));
    render(<App />);
    fireEvent.change(screen.getByLabelText("Email address"), { target: { value: "student@example.com" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "ComplexPass123!" } });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));
    expect(screen.getByRole("button", { name: "Signing in…" })).toBeDisabled();
    resolveLogin(response(200, storedSession("student")));
    expect(await screen.findByRole("heading", { name: "Student area" })).toBeInTheDocument();
  });

  it("establishes a session and routes a successful login", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(response(200, storedSession("student")));
    render(<App />);
    await userEvent.type(screen.getByLabelText("Email address"), "student@example.com");
    await userEvent.type(screen.getByLabelText("Password"), "ComplexPass123!");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));
    expect(await screen.findByRole("heading", { name: "Student area" })).toBeInTheDocument();
    expect(sessionStorage.getItem(sessionKey)).not.toBeNull();
  });

  it("redirects an unauthenticated protected route to login", async () => {
    window.history.replaceState({}, "", "/student/");
    render(<App />);
    await waitFor(() => expect(window.location.pathname).toBe("/login/"));
    expect(await screen.findByRole("heading", { name: "Sign in to AAIAPP" })).toBeInTheDocument();
  });

  it.each([
    ["student", "/student/", "Student area"],
    ["supervisor", "/supervisor/", "Supervisor area"],
    ["administrator", "/admin/", "Administrator area"],
  ] as const)("validates and opens the %s route", async (role, path, heading) => {
    sessionStorage.setItem(sessionKey, JSON.stringify(storedSession(role)));
    window.history.replaceState({}, "", path);
    vi.spyOn(globalThis, "fetch").mockResolvedValue(response(200, users[role]));
    render(<App />);
    expect(await screen.findByRole("heading", { name: heading })).toBeInTheDocument();
  });

  it.each([
    ["student", "/supervisor/", "/student/"],
    ["student", "/admin/", "/student/"],
    ["supervisor", "/admin/", "/supervisor/"],
  ] as const)("redirects a %s away from a forbidden role route", async (role, path, expected) => {
    sessionStorage.setItem(sessionKey, JSON.stringify(storedSession(role)));
    window.history.replaceState({}, "", path);
    vi.spyOn(globalThis, "fetch").mockResolvedValue(response(200, users[role]));
    render(<App />);
    await waitFor(() => expect(window.location.pathname).toBe(expected));
  });

  it("uses the backend role instead of a manipulated stored role", async () => {
    sessionStorage.setItem(sessionKey, JSON.stringify(storedSession("administrator")));
    window.history.replaceState({}, "", "/admin/");
    vi.spyOn(globalThis, "fetch").mockResolvedValue(response(200, users.student));
    render(<App />);
    await waitFor(() => expect(window.location.pathname).toBe("/student/"));
    expect(await screen.findByRole("heading", { name: "Student area" })).toBeInTheDocument();
  });

  it("refreshes an expired restored session and validates it", async () => {
    sessionStorage.setItem(sessionKey, JSON.stringify(storedSession("student")));
    window.history.replaceState({}, "", "/student/");
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(response(401))
      .mockResolvedValueOnce(response(200, { access: "new-access", refresh: "new-refresh" }))
      .mockResolvedValueOnce(response(200, users.student));
    render(<App />);
    expect(await screen.findByRole("heading", { name: "Student area" })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(sessionStorage.getItem(sessionKey)).toContain("new-access");
  });

  it("clears an invalid restored session when refresh fails", async () => {
    sessionStorage.setItem(sessionKey, JSON.stringify(storedSession("student")));
    window.history.replaceState({}, "", "/student/");
    vi.spyOn(globalThis, "fetch").mockResolvedValue(response(401));
    render(<App />);
    expect(await screen.findByRole("heading", { name: "Sign in to AAIAPP" })).toBeInTheDocument();
    expect(sessionStorage.getItem(sessionKey)).toBeNull();
  });

  it("clears a restored session when the backend reports an inactive user", async () => {
    sessionStorage.setItem(sessionKey, JSON.stringify(storedSession("student")));
    window.history.replaceState({}, "", "/student/");
    vi.spyOn(globalThis, "fetch").mockResolvedValue(response(200, { ...users.student, status: "deactivated" }));
    render(<App />);
    expect(await screen.findByRole("heading", { name: "Sign in to AAIAPP" })).toBeInTheDocument();
    expect(sessionStorage.getItem(sessionKey)).toBeNull();
  });

  it("logs out through the backend, clears storage, and navigates to login", async () => {
    sessionStorage.setItem(sessionKey, JSON.stringify(storedSession("student")));
    window.history.replaceState({}, "", "/student/");
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(response(200, users.student))
      .mockResolvedValueOnce(response(204));
    render(<App />);
    await userEvent.click(await screen.findByRole("button", { name: "Sign out" }));
    await waitFor(() => expect(window.location.pathname).toBe("/login/"));
    expect(sessionStorage.getItem(sessionKey)).toBeNull();
    expect(fetchMock.mock.calls[1][0]).toContain("/api/auth/logout/");
    expect(fetchMock.mock.calls[1][1]?.headers).toMatchObject({ Authorization: "Bearer access" });
  });
});
