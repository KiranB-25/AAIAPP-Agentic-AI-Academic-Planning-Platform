import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import App from "../App";
import { sessionKey } from "../auth/session-store";
import type { AcademicGoal } from "../types/goals";

const user = { id: 1, name: "Student", email: "student@example.com", role: "student" as const, status: "active" as const };
const goal: AcademicGoal = {
  id: 7,
  subject: "Data Structures",
  description: "Master trees, graphs, and efficient data organization.",
  duration: 8,
  intensity: "Moderate",
  status: "pending",
  is_editable: true,
  created_at: "2026-08-16T10:00:00Z",
  updated_at: "2026-08-16T10:00:00Z",
};

function response(status: number, body?: unknown) {
  return new Response(body === undefined ? null : JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function authenticate() {
  sessionStorage.setItem(sessionKey, JSON.stringify({ access: "access", refresh: "refresh", user }));
}

function mockPage(goals: AcademicGoal[] = []) {
  return vi.spyOn(globalThis, "fetch")
    .mockResolvedValueOnce(response(200, user))
    .mockResolvedValueOnce(response(200, goals));
}

describe("Student academic goals", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    sessionStorage.clear();
    window.history.replaceState({}, "", "/student/goals/");
  });

  it("renders the protected goal page", async () => {
    authenticate();
    mockPage();
    render(<App />);
    expect(await screen.findByRole("heading", { name: "Academic goals" })).toBeInTheDocument();
  });

  it("shows a loading state while goals are requested", async () => {
    authenticate();
    let resolveGoals!: (value: Response) => void;
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(response(200, user))
      .mockImplementationOnce(() => new Promise((resolve) => { resolveGoals = resolve; }));
    render(<App />);
    expect(await screen.findByText("Loading academic goals…")).toBeInTheDocument();
    resolveGoals(response(200, []));
    expect(await screen.findByText("No academic goals yet")).toBeInTheDocument();
  });

  it("renders the empty state", async () => {
    authenticate();
    mockPage();
    render(<App />);
    expect(await screen.findByRole("heading", { name: "No academic goals yet" })).toBeInTheDocument();
  });

  it("renders goals returned by the API", async () => {
    authenticate();
    mockPage([goal]);
    render(<App />);
    expect(await screen.findByRole("heading", { name: goal.subject })).toBeInTheDocument();
    expect(screen.getByText("8 weeks")).toBeInTheDocument();
    expect(screen.getByText(goal.description)).toBeInTheDocument();
  });

  it("validates required goal fields", async () => {
    authenticate();
    mockPage();
    render(<App />);
    await userEvent.click(await screen.findByRole("button", { name: "New goal" }));
    await userEvent.click(screen.getByRole("button", { name: "Create goal" }));
    expect(screen.getByText("Subject is required.")).toBeInTheDocument();
    expect(screen.getByText("Objective or description is required.")).toBeInTheDocument();
    expect(screen.getByText("Duration is required.")).toBeInTheDocument();
  });

  it("rejects an out-of-range duration before submission", async () => {
    authenticate();
    const fetchMock = mockPage();
    render(<App />);
    await userEvent.click(await screen.findByRole("button", { name: "New goal" }));
    await userEvent.type(screen.getByLabelText("Subject"), "Algorithms");
    await userEvent.type(screen.getByLabelText("Objective or description"), "Learn algorithm design.");
    await userEvent.type(screen.getByLabelText("Duration in weeks"), "17");
    await userEvent.click(screen.getByRole("button", { name: "Create goal" }));
    expect(screen.getByText("Duration must be between 1 and 16 weeks.")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("creates a goal and updates the interface", async () => {
    authenticate();
    mockPage();
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(response(201, goal));
    render(<App />);
    await userEvent.click(await screen.findByRole("button", { name: "New goal" }));
    await userEvent.type(screen.getByLabelText("Subject"), goal.subject);
    await userEvent.type(screen.getByLabelText("Objective or description"), goal.description);
    await userEvent.type(screen.getByLabelText("Duration in weeks"), String(goal.duration));
    await userEvent.type(screen.getByLabelText(/Study intensity/), goal.intensity);
    await userEvent.click(screen.getByRole("button", { name: "Create goal" }));
    expect(await screen.findByText("Academic goal created successfully.")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: goal.subject })).toBeInTheDocument();
  });

  it("shows backend creation validation errors", async () => {
    authenticate();
    mockPage();
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(response(400, { subject: ["This subject is not valid."] }));
    render(<App />);
    await userEvent.click(await screen.findByRole("button", { name: "New goal" }));
    await userEvent.type(screen.getByLabelText("Subject"), goal.subject);
    await userEvent.type(screen.getByLabelText("Objective or description"), goal.description);
    await userEvent.type(screen.getByLabelText("Duration in weeks"), "8");
    await userEvent.click(screen.getByRole("button", { name: "Create goal" }));
    expect(await screen.findByText("This subject is not valid.")).toBeInTheDocument();
  });

  it("loads existing data into the edit form", async () => {
    authenticate();
    mockPage([goal]);
    render(<App />);
    await userEvent.click(await screen.findByRole("button", { name: "View details" }));
    await userEvent.click(screen.getByRole("button", { name: "Edit goal" }));
    expect(screen.getByLabelText("Subject")).toHaveValue(goal.subject);
    expect(screen.getByLabelText("Objective or description")).toHaveValue(goal.description);
    expect(screen.getByLabelText("Duration in weeks")).toHaveValue(goal.duration);
  });

  it("updates an editable goal", async () => {
    authenticate();
    mockPage([goal]);
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(response(200, { ...goal, subject: "Advanced Algorithms" }));
    render(<App />);
    await userEvent.click(await screen.findByRole("button", { name: "View details" }));
    await userEvent.click(screen.getByRole("button", { name: "Edit goal" }));
    await userEvent.clear(screen.getByLabelText("Subject"));
    await userEvent.type(screen.getByLabelText("Subject"), "Advanced Algorithms");
    await userEvent.click(screen.getByRole("button", { name: "Save changes" }));
    expect(await screen.findByText("Academic goal updated successfully.")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Advanced Algorithms" })).toBeInTheDocument();
  });

  it("does not offer editing for a non-editable goal", async () => {
    authenticate();
    mockPage([{ ...goal, is_editable: false }]);
    render(<App />);
    await userEvent.click(await screen.findByRole("button", { name: "View details" }));
    expect(screen.queryByRole("button", { name: "Edit goal" })).not.toBeInTheDocument();
  });

  it("shows a goal loading API error", async () => {
    authenticate();
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(response(200, user))
      .mockResolvedValueOnce(response(500, { detail: "Unable to load goals." }));
    render(<App />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Unable to load goals.");
  });

  it("redirects unauthenticated users to login", async () => {
    render(<App />);
    await waitFor(() => expect(window.location.pathname).toBe("/login/"));
    expect(await screen.findByRole("heading", { name: "Sign in to AAIAPP" })).toBeInTheDocument();
  });
});
