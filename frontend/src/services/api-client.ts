const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

import { clearSession, readSession, storeSession } from "../auth/session-store";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
    public readonly fieldErrors?: Record<string, string[]>,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

interface RequestOptions {
  authenticated?: boolean;
  accessToken?: string;
  retryOnUnauthorized?: boolean;
}

interface RefreshResponse {
  access: string;
  refresh?: string;
}

let refreshRequest: Promise<string> | null = null;

async function refreshAccessToken(): Promise<string> {
  if (refreshRequest) return refreshRequest;
  refreshRequest = (async () => {
    const session = readSession();
    if (!session) throw new ApiError("Your session has expired.", 401);
    const response = await fetch(`${apiBaseUrl}/api/auth/token/refresh/`, {
      method: "POST",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      body: JSON.stringify({ refresh: session.refresh }),
    });
    if (!response.ok) throw new ApiError("Your session has expired.", response.status);
    const tokens = await response.json() as RefreshResponse;
    storeSession({ ...session, access: tokens.access, refresh: tokens.refresh ?? session.refresh });
    return tokens.access;
  })();
  try {
    return await refreshRequest;
  } finally {
    refreshRequest = null;
  }
}

async function send(path: string, init: RequestInit, accessToken?: string): Promise<Response> {
  try {
    return await fetch(`${apiBaseUrl}${path}`, {
      ...init,
      headers: {
        Accept: "application/json",
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        ...init.headers,
      },
    });
  } catch {
    throw new ApiError("Unable to reach the backend API.");
  }
}

async function request<T>(path: string, init: RequestInit, options: RequestOptions = {}): Promise<T> {
  const authenticated = options.authenticated ?? false;
  const accessToken = options.accessToken ?? (authenticated ? readSession()?.access : undefined);
  let response: Response;
  response = await send(path, init, accessToken);

  if (response.status === 401 && authenticated && (options.retryOnUnauthorized ?? true)) {
    try {
      const refreshedAccess = await refreshAccessToken();
      response = await send(path, init, refreshedAccess);
    } catch (error) {
      clearSession(true);
      throw error;
    }
    if (response.status === 401) clearSession(true);
  }

  if (!response.ok) {
    const body = await response.json().catch(() => null) as Record<string, unknown> | null;
    const detail = typeof body?.detail === "string" ? body.detail : "The backend API returned an unexpected response.";
    const fieldErrors = body
      ? Object.fromEntries(Object.entries(body).filter(([, value]) => Array.isArray(value))) as Record<string, string[]>
      : undefined;
    throw new ApiError(detail, response.status, fieldErrors);
  }

  return response.status === 204 ? undefined as T : await response.json() as T;
}

export function get<T>(path: string, options?: RequestOptions): Promise<T> {
  return request<T>(path, { method: "GET" }, options);
}

export function post<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
  return request<T>(path, {
    method: "POST",
    headers: body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  }, options);
}

export function patch<T>(path: string, body: unknown, options?: RequestOptions): Promise<T> {
  return request<T>(path, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }, options);
}

export async function download(path: string, options: RequestOptions = {}): Promise<Blob> {
  const authenticated = options.authenticated ?? false;
  let response = await send(path, { method: "GET" }, options.accessToken ?? (authenticated ? readSession()?.access : undefined));
  if (response.status === 401 && authenticated && (options.retryOnUnauthorized ?? true)) {
    try {
      response = await send(path, { method: "GET" }, await refreshAccessToken());
    } catch (error) {
      clearSession(true);
      throw error;
    }
    if (response.status === 401) clearSession(true);
  }
  if (!response.ok) throw new ApiError("The export could not be completed.", response.status);
  return response.blob();
}
