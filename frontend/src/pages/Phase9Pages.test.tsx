import { render, screen } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";
import App from "../App";
import { sessionKey } from "../auth/session-store";

const supervisor = { id: 2, name: "Supervisor", email: "supervisor@example.com", role: "supervisor", status: "active" };
const student = { id: 1, name: "Student", email: "student@example.com", role: "student", status: "active" };
const response = (body: unknown) => new Response(JSON.stringify(body), { status: 200, headers: { "Content-Type": "application/json" } });

beforeEach(() => { vi.restoreAllMocks(); sessionStorage.clear(); });

it("renders assigned supervisor plans and review controls", async () => {
  sessionStorage.setItem(sessionKey, JSON.stringify({ access: "a", refresh: "r", user: supervisor })); window.history.replaceState({}, "", "/supervisor/plans/");
  vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(response(supervisor)).mockResolvedValueOnce(response([{ id: 3, goal_id: 7, generated_at: "", summary: "Algorithms plan", status: "generated", progress: 50, tasks: [] }]));
  render(<App />);
  expect(await screen.findByText("Algorithms plan")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Approve plan" })).toBeInTheDocument();
});

it("renders student feedback, notification count, and mark-read control", async () => {
  sessionStorage.setItem(sessionKey, JSON.stringify({ access: "a", refresh: "r", user: student })); window.history.replaceState({}, "", "/student/reviews/");
  vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(response(student)).mockResolvedValueOnce(response([{ id: 1, study_plan_id: 3, feedback_text: "Well structured", decision: "approved", created_at: "", updated_at: "" }])).mockResolvedValueOnce(response([{ id: 2, notification_type: "plan_approved", title: "Study plan approved", message: "Feedback is ready.", study_plan_id: 3, created_at: "", read_at: null }])).mockResolvedValueOnce(response({ unread_count: 1 }));
  render(<App />);
  expect(await screen.findByText("Well structured")).toBeInTheDocument();
  expect(screen.getByLabelText("1 unread notifications")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Mark as read" })).toBeInTheDocument();
});
