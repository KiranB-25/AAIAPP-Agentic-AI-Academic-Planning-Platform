import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import App from "../App";
import { sessionKey } from "../auth/session-store";

const user = { id: 1, name: "Student", email: "student@example.com", role: "student", status: "active" };
const goal = { id: 7, subject: "Algorithms", description: "Learn algorithms", duration: 4, intensity: "Moderate", status: "plan_generated", is_editable: false, created_at: "2026-08-16T10:00:00Z", updated_at: "2026-08-16T10:00:00Z" };
const task = { id: 10, week: 1, title: "Foundations", description: "Study foundations", method: "Active recall", objective: "Understand core concepts", revision_checkpoint: true, is_completed: false, completed_at: null, updated_at: "2026-08-16T10:00:00Z" };
const plan = { id: 3, goal_id: 7, generated_at: "2026-08-16T10:00:00Z", summary: "An ordered plan", status: "generated", progress: 0, tasks: [task] };

function response(status: number, body: unknown) { return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } }); }
function authenticate() { sessionStorage.setItem(sessionKey, JSON.stringify({ access: "access", refresh: "refresh", user })); }

describe("Student study plans", () => {
  beforeEach(() => { vi.restoreAllMocks(); sessionStorage.clear(); window.history.replaceState({}, "", "/student/plans/"); authenticate(); });

  it("shows loading then the empty state", async () => {
    let resolvePlans!: (response: Response) => void;
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(response(200, user)).mockImplementationOnce(() => new Promise((resolve) => { resolvePlans = resolve; })).mockResolvedValueOnce(response(200, []));
    render(<App />);
    expect(await screen.findByText("Loading study plans…")).toBeInTheDocument();
    await waitFor(() => expect(resolvePlans).toBeTypeOf("function"));
    resolvePlans(response(200, []));
    expect(await screen.findByRole("heading", { name: "No study plan yet" })).toBeInTheDocument();
  });

  it("renders ordered plan content and accessible completion control", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(response(200, user)).mockResolvedValueOnce(response(200, [plan])).mockResolvedValueOnce(response(200, [goal]));
    render(<App />);
    expect(await screen.findByRole("heading", { name: "Algorithms" })).toBeInTheDocument();
    expect(screen.getByText("Week 1")).toBeInTheDocument();
    expect(screen.getByText("Understand core concepts")).toBeInTheDocument();
    expect(screen.getByText("Revision checkpoint")).toBeInTheDocument();
    expect(screen.getByRole("checkbox", { name: "Mark Foundations complete" })).toBeInTheDocument();
    expect(screen.getByLabelText("Progress 0%")).toBeInTheDocument();
  });

  it("updates completion and progress from the confirmed API response", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(response(200, user)).mockResolvedValueOnce(response(200, [plan])).mockResolvedValueOnce(response(200, [goal])).mockResolvedValueOnce(response(200, { task: { ...task, is_completed: true, completed_at: "2026-08-16T11:00:00Z" }, progress: 100 }));
    render(<App />);
    await userEvent.click(await screen.findByRole("checkbox", { name: "Mark Foundations complete" }));
    expect(await screen.findByLabelText("Progress 100%")).toBeInTheDocument();
    expect(screen.getByText("Completed")).toBeInTheDocument();
  });

  it("offers generation for a pending goal", async () => {
    const pending = { ...goal, status: "pending", is_editable: true };
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(response(200, user)).mockResolvedValueOnce(response(200, [])).mockResolvedValueOnce(response(200, [pending])).mockResolvedValueOnce(response(201, plan));
    render(<App />);
    await userEvent.click(await screen.findByRole("button", { name: "Generate plan for Algorithms" }));
    expect(await screen.findByRole("heading", { name: "Algorithms" })).toBeInTheDocument();
  });

  it("shows a safe API error and retry action", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(response(200, user)).mockResolvedValueOnce(response(500, { detail: "Internal provider trace" })).mockResolvedValueOnce(response(200, []));
    render(<App />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Unable to load your study plans");
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });
});
