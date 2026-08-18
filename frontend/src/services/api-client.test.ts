import { beforeEach, describe, expect, it, vi } from "vitest";

import { readSession, sessionKey } from "../auth/session-store";
import type { AuthSession } from "../types/auth";
import { ApiError, get } from "./api-client";

const session: AuthSession = {
  access: "old-access",
  refresh: "old-refresh",
  user: { id: 1, name: "Student", email: "student@example.com", role: "student", status: "active" },
};

function response(status: number, body?: unknown) {
  return new Response(body === undefined ? null : JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("authenticated API requests", () => {
  beforeEach(() => {
    sessionStorage.clear();
    sessionStorage.setItem(sessionKey, JSON.stringify(session));
    window.history.replaceState({}, "", "/student/");
    vi.restoreAllMocks();
  });

  it("refreshes once, stores rotated tokens, and retries the original request", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(response(401, { detail: "expired" }))
      .mockResolvedValueOnce(response(200, { access: "new-access", refresh: "new-refresh" }))
      .mockResolvedValueOnce(response(200, { value: "ok" }));

    await expect(get<{ value: string }>("/protected/", { authenticated: true })).resolves.toEqual({ value: "ok" });
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(fetchMock.mock.calls[2][1]?.headers).toMatchObject({ Authorization: "Bearer new-access" });
    expect(readSession()).toMatchObject({ access: "new-access", refresh: "new-refresh" });
  });

  it("shares one refresh request between simultaneous 401 responses", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(response(401))
      .mockResolvedValueOnce(response(401))
      .mockResolvedValueOnce(response(200, { access: "new-access", refresh: "new-refresh" }))
      .mockResolvedValueOnce(response(200, { first: true }))
      .mockResolvedValueOnce(response(200, { second: true }));

    await Promise.all([
      get("/first/", { authenticated: true }),
      get("/second/", { authenticated: true }),
    ]);
    const refreshCalls = fetchMock.mock.calls.filter(([url]) => String(url).endsWith("/api/auth/token/refresh/"));
    expect(refreshCalls).toHaveLength(1);
  });

  it("clears the session and redirects when refresh fails", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(response(401))
      .mockResolvedValueOnce(response(401, { detail: "invalid refresh" }));

    await expect(get("/protected/", { authenticated: true })).rejects.toBeInstanceOf(ApiError);
    expect(readSession()).toBeNull();
    expect(window.location.pathname).toBe("/login/");
  });

  it("does not refresh a forbidden response", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(response(403, { detail: "forbidden" }));

    await expect(get("/admin/", { authenticated: true })).rejects.toMatchObject({ status: 403 });
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(readSession()).not.toBeNull();
  });

  it("retries only once and clears a session when the retried request is still unauthorized", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(response(401))
      .mockResolvedValueOnce(response(200, { access: "new-access", refresh: "new-refresh" }))
      .mockResolvedValueOnce(response(401));

    await expect(get("/protected/", { authenticated: true })).rejects.toMatchObject({ status: 401 });
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(readSession()).toBeNull();
  });
});
